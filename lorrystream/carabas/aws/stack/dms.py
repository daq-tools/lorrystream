import json
import typing as t

import attr
import cottonformation as cf
from cottonformation import GetAtt
from cottonformation.res import awslambda, ec2, iam, kinesis, rds

from lorrystream.carabas.aws import LambdaFactory
from lorrystream.carabas.aws.cf import dms_next as dms
from lorrystream.carabas.aws.model import KinesisProcessorStack


@attr.s
class RDSPostgreSQLDMSKinesisPipe(KinesisProcessorStack):
    """
    A description for an AWS CloudFormation stack for migrating from PostgreSQL.
    It is written down in Python, uses OO, and a fluent API.

    It provides elements to implement this kind of pipeline:

        RDS PostgreSQL -> DMS -> Kinesis Stream -> Python Lambda via OCI -> CrateDB

    See also the canonical AWS documentation about relevant topics.

    Documentation:
    - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Serverless.Components.html
    - https://docs.aws.amazon.com/dms/latest/userguide/CHAP_VPC_Endpoints.html
    - https://docs.aws.amazon.com/dms/latest/userguide/security-iam-awsmanpol.html
    - https://docs.aws.amazon.com/dms/latest/userguide/security-iam.html#CHAP_Security.IAMPermissions

    Resources:
    - https://aws.amazon.com/blogs/database/orchestrate-an-aws-dms-serverless-replication-task-using-aws-cli/
    - https://aws.amazon.com/blogs/aws/new-aws-dms-serverless-automatically-provisions-and-scales-capacity-for-migration-and-data-replication/
    - https://github.com/aws-cloudformation/aws-cloudformation-templates/blob/main/DMS/DMSAuroraToS3FullLoadAndOngoingReplication.yaml
    """

    db_username: str = attr.ib()
    db_password: str = attr.ib()

    _vpc: ec2.VPC = None
    _public_subnet1: ec2.Subnet = None
    _public_subnet2: ec2.Subnet = None
    _db_subnet_group: rds.DBSubnetGroup = None
    _db_security_group: ec2.SecurityGroup = None

    _db: rds.DBInstance = None

    _dms_instance: dms.ReplicationInstance = None
    _dms_kinesis_access_role: iam.Role = None

    def vpc(self):
        group = cf.ResourceGroup()

        self._vpc = ec2.VPC(
            "VPCInstance",
            p_CidrBlock="10.0.0.0/24",
            p_EnableDnsHostnames=True,
            p_EnableDnsSupport=True,
            p_Tags=cf.Tag.make_many(
                Name=cf.Sub.from_params(f"{self.env_name}-vpc"),
                Description=cf.Sub.from_params(f"The VPC for {self.env_name}"),
            ),
        )
        group.add(self._vpc)

        # Even if you are deploying a single-az instance, you have to
        # specify multiple availability zones in the DB subnet group.
        # https://stackoverflow.com/a/70658040
        # https://stackoverflow.com/a/63975208
        self._public_subnet1 = ec2.Subnet(
            "VPCPublicSubnet1",
            p_CidrBlock="10.0.0.0/26",
            rp_VpcId=self._vpc.ref(),
            p_AvailabilityZone=cf.GetAZs.n_th(1),
            p_MapPublicIpOnLaunch=False,
            p_Tags=cf.Tag.make_many(
                Name=cf.Sub.from_params(f"{self.env_name}-vpc-subnet1"),
                Description=cf.Sub.from_params(f"The VPC subnet 1 for {self.env_name}"),
            ),
            ra_DependsOn=self._vpc,
        )
        self._public_subnet2 = ec2.Subnet(
            "VPCPublicSubnet2",
            p_CidrBlock="10.0.0.64/26",
            rp_VpcId=self._vpc.ref(),
            p_AvailabilityZone=cf.GetAZs.n_th(2),
            p_MapPublicIpOnLaunch=False,
            p_Tags=cf.Tag.make_many(
                Name=cf.Sub.from_params(f"{self.env_name}-vpc-subnet2"),
                Description=cf.Sub.from_params(f"The VPC subnet 2 for {self.env_name}"),
            ),
            ra_DependsOn=self._vpc,
        )
        group.add(self._public_subnet1)
        group.add(self._public_subnet2)

        # FIXME: Problem: Cannot create a publicly accessible DBInstance.
        #        The specified VPC has no internet gateway attached.
        gateway = ec2.InternetGateway(
            "VPCGateway",
            p_Tags=cf.Tag.make_many(
                Name=cf.Sub.from_params(f"{self.env_name}-vpc-gateway"),
                Description=cf.Sub.from_params(f"The VPC gateway for {self.env_name}"),
            ),
            ra_DependsOn=self._vpc,
        )
        gateway_attachment = ec2.VPCGatewayAttachment(
            "VPCGatewayAttachment",
            rp_VpcId=self._vpc.ref(),
            p_InternetGatewayId=gateway.ref(),
            ra_DependsOn=[self._vpc, gateway],
        )
        group.add(gateway)
        group.add(gateway_attachment)

        route_table = ec2.RouteTable(
            "VPCRouteTable",
            rp_VpcId=self._vpc.ref(),
            p_Tags=cf.Tag.make_many(
                Name=cf.Sub.from_params(f"{self.env_name}-vpc-route-table"),
                Description=cf.Sub.from_params(f"The VPC routing table for {self.env_name}"),
            ),
        )
        group.add(route_table)

        default_route = ec2.Route(
            "VPCDefaultRoute",
            rp_RouteTableId=route_table.ref(),
            p_DestinationCidrBlock="0.0.0.0/0",
            p_GatewayId=gateway.ref(),
            ra_DependsOn=gateway_attachment,
        )
        group.add(default_route)

        subnet_route_1 = ec2.SubnetRouteTableAssociation(
            "VPCSubnetRoute1",
            rp_RouteTableId=route_table.ref(),
            rp_SubnetId=self._public_subnet1.ref(),
            ra_DependsOn=[route_table, self._public_subnet1],
        )
        subnet_route_2 = ec2.SubnetRouteTableAssociation(
            "VPCSubnetRoute2",
            rp_RouteTableId=route_table.ref(),
            rp_SubnetId=self._public_subnet2.ref(),
            ra_DependsOn=[route_table, self._public_subnet2],
        )
        group.add(subnet_route_1)
        group.add(subnet_route_2)

        return self.add(group)

    def database(self):
        group = cf.ResourceGroup()

        # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html
        self._db_subnet_group = rds.DBSubnetGroup(
            "RDSPostgreSQLDBSubnetGroup",
            rp_DBSubnetGroupDescription=f"DB subnet group for {self.env_name}",
            rp_SubnetIds=[self._public_subnet1.ref(), self._public_subnet2.ref()],
            p_DBSubnetGroupName=f"{self.env_name}-db-subnet-group",
            p_Tags=cf.Tag.make_many(Name=cf.Sub.from_params(f"{self.env_name}-db-subnet-group")),
            ra_DependsOn=[self._public_subnet1, self._public_subnet2],
        )
        group.add(self._db_subnet_group)

        db_security_group_name = f"{self.env_name}-db-security-group"
        self._db_security_group = ec2.SecurityGroup(
            "RDSPostgreSQLSecurityGroup",
            rp_GroupDescription=f"DB security group for {self.env_name}",
            p_GroupName=db_security_group_name,
            p_VpcId=self._vpc.ref(),
            p_SecurityGroupIngress=[
                ec2.PropSecurityGroupIngress(
                    rp_IpProtocol="TCP",
                    p_Description="Allow access from VPC",
                    p_FromPort=5432,
                    p_ToPort=5432,
                    p_CidrIp="10.0.0.0/24",
                ),
                # TODO: Possibly restrict to single provided ClientIP?
                ec2.PropSecurityGroupIngress(
                    rp_IpProtocol="TCP",
                    p_Description="Allow access from outside",
                    p_FromPort=5432,
                    p_ToPort=5432,
                    p_CidrIp="0.0.0.0/0",
                ),
            ],
            p_SecurityGroupEgress=[
                ec2.PropSecurityGroupEgress(
                    rp_IpProtocol="-1",
                    p_Description="Allow any access out",
                    p_FromPort=-1,
                    p_ToPort=-1,
                    p_CidrIp="0.0.0.0/0",
                )
            ],
            p_Tags=cf.Tag.make_many(Name=cf.Sub.from_params(db_security_group_name)),
            ra_DependsOn=[self._vpc],
        )
        group.add(self._db_security_group)

        # aws rds describe-db-parameter-groups
        # aws rds describe-db-parameters --db-parameter-group-name default.postgres15
        db_parameter_group = rds.DBParameterGroup(
            "RDSPostgreSQLParameterGroup",
            rp_Family="postgres15",
            rp_Description="DMS parameter group for postgres15",
            p_DBParameterGroupName="dms-postgres15",
            # aws rds describe-db-parameters --db-parameter-group-name default.postgres15
            p_Parameters={
                "log_connections": True,
                # List of allowable settings for the pgaudit.log parameter:
                # none, all, ddl, function, misc, read, role, write
                # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.pgaudit.html
                "pgaudit.log": "none",
                "pgaudit.log_statement_once": True,
                # `rds.logical_replication is a cluster level setting, not db instance setting?
                # https://stackoverflow.com/a/66252465
                "rds.logical_replication": True,
                "shared_preload_libraries": "pgaudit,pglogical,pg_stat_statements",
            },
        )
        group.add(db_parameter_group)

        db = rds.DBInstance(
            "RDSPostgreSQL",
            p_DBInstanceClass="db.t3.micro",
            p_DBInstanceIdentifier=f"{self.env_name}-db",
            p_Engine="postgres",
            # PostgreSQL 16 only supported by DMS 3.5.3.
            # The current default engine version for AWS DMS is 3.5.2.
            # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_ReleaseNotes.html
            p_EngineVersion="15",
            p_DBParameterGroupName="dms-postgres15",
            # The parameter AllocatedStorage must be provided and must not be null.
            # Invalid storage size for engine name postgres and storage type gp2: 1
            p_AllocatedStorage="5",
            # p_StorageType="gp3",  # noqa: ERA001
            # Setting this parameter to 0 disables automated backups.
            # Disabling automated backups speeds up the provisioning process.
            p_BackupRetentionPeriod=0,
            # To disable collection of Enhanced Monitoring metrics, specify 0.
            p_MonitoringInterval=0,
            p_EnablePerformanceInsights=False,
            p_MasterUsername=self.db_username,
            p_MasterUserPassword=self.db_password,
            p_PubliclyAccessible=True,
            p_MultiAZ=False,
            p_VPCSecurityGroups=[
                self._db_security_group.ref(),
            ],
            # If there's no DB subnet group, then the DB instance isn't a VPC DB instance.
            p_DBSubnetGroupName=self._db_subnet_group.ref(),
            p_EnableCloudwatchLogsExports=["postgresql"],
            # p_DBName="testdrive",  # noqa: ERA001
            p_Tags=cf.Tag.make_many(
                Name=cf.Sub.from_params(f"{self.env_name}-db"),
                Description=cf.Sub.from_params(f"The DB instance for {self.env_name}"),
            ),
            ra_DependsOn=[db_parameter_group, self._db_security_group, self._db_subnet_group],
        )
        self._db = db
        group.add(db)

        rds_arn = cf.Output(
            "RDSInstanceArn",
            Value=db.rv_DBInstanceArn,
        )
        group.add(rds_arn)

        public_endpoint = cf.Output(
            "DatabaseHost",
            Value=db.rv_EndpointAddress,
        )
        group.add(public_endpoint)

        public_db_port = cf.Output(
            "DatabasePort",
            Value=db.rv_EndpointPort,
        )
        group.add(public_db_port)
        return self.add(group)

    def stream(self):
        group = cf.ResourceGroup()
        # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Target.Kinesis.html#CHAP_Target.Kinesis.Prerequisites

        self._stream_source = kinesis.Stream(
            id="KinesisStream",
            p_Name=f"{self.env_name}-stream",
            p_StreamModeDetails={"rp_StreamMode": "ON_DEMAND"},
        )
        stream_arn = cf.Output(
            "StreamArn",
            Value=self._stream_source.rv_Arn,
        )
        group.add(self._stream_source)
        group.add(stream_arn)
        return self.add(group)

    def dms(self):
        """
        An AWS DMS Serverless CloudFormation description for demonstration purposes.

        https://docs.aws.amazon.com/dms/latest/userguide/security-iam.html#CHAP_Security.APIRole

        Database Migration Service requires the below IAM Roles to be created before
        replication instances can be created. See the DMS Documentation for
        additional information: https://docs.aws.amazon.com/dms/latest/userguide/security-iam.html#CHAP_Security.APIRole
        * dms-vpc-role
        * dms-cloudwatch-logs-role
        * dms-access-for-endpoint

        If you use the AWS CLI or the AWS DMS API for your database migration, you must add three IAM roles
        to your AWS account before you can use the features of AWS DMS. Two of these are `dms-vpc-role` and
        `dms-cloudwatch-logs-role`.

        If you use Amazon Redshift as a target database, you must also add the IAM role
        `dms-access-for-endpoint` to your AWS account.

        -- https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dms_replication_instance.html
        -- https://github.com/hashicorp/terraform-provider-aws/issues/19580
        -- https://docs.aws.amazon.com/dms/latest/userguide/security-iam.html#CHAP_Security.APIRole
        """
        group = cf.ResourceGroup()

        # Trust policy that is associated with upcoming roles.
        # Trust policies define which entities can assume the role.
        # You can associate only one trust policy with a role.
        trust_policy_dms = cf.helpers.iam.AssumeRolePolicyBuilder(
            cf.helpers.iam.ServicePrincipal.dms(),
        ).build()

        dms_vpc_role = iam.Role(
            id="DMSVPCManagementRole",
            rp_AssumeRolePolicyDocument=trust_policy_dms,
            # Role name must strictly be `dms-vpc-role`?
            # https://stackoverflow.com/q/58542334
            # https://github.com/hashicorp/terraform-provider-aws/issues/7748
            # https://github.com/hashicorp/terraform-provider-aws/issues/11025
            # p_RoleName=cf.Sub("${EnvName}-dms-vpc-role", {"EnvName": self.param_env_name.ref()}),  # noqa: ERA001, E501
            p_RoleName="dms-vpc-role",
            p_Description="DMS VPC management IAM role",
            p_ManagedPolicyArns=[
                cf.helpers.iam.AwsManagedPolicy.AmazonDMSVPCManagementRole,
            ],
        )
        group.add(dms_vpc_role)
        dms_cloudwatch_role = iam.Role(
            id="DMSCloudWatchLogsRole",
            rp_AssumeRolePolicyDocument=trust_policy_dms,
            # Role name must strictly be `dms-cloudwatch-logs-role`?
            # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Troubleshooting.html#CHAP_Troubleshooting.General.CWL
            # p_RoleName=cf.Sub("${EnvName}-dms-cloudwatch-logs-role", {"EnvName": self.param_env_name.ref()}),  # noqa: ERA001, E501
            p_RoleName="dms-cloudwatch-logs-role",
            p_Description="DMS CloudWatch IAM role",
            p_ManagedPolicyArns=[
                cf.helpers.iam.AwsManagedPolicy.AmazonDMSCloudWatchLogsRole,
            ],
        )
        group.add(dms_cloudwatch_role)

        # Allow DMS accessing the data sink. In this case, Kinesis.
        # For Redshift, this role needs to be called `dms-access-for-endpoint`.
        self._dms_kinesis_access_role = iam.Role(
            id="DMSTargetAccessRole",
            rp_AssumeRolePolicyDocument=trust_policy_dms,
            p_RoleName=cf.Sub("${EnvName}-dms-target-access-role", {"EnvName": self.param_env_name.ref()}),
            p_Description="DMS target access IAM role",
            p_ManagedPolicyArns=[
                cf.helpers.iam.AwsManagedPolicy.AmazonKinesisFullAccess,
            ],
            ra_DependsOn=self._stream_source,
        )
        group.add(self._dms_kinesis_access_role)

        # Create a replication subnet group given a list of the subnet IDs in a VPC.
        # https://docs.aws.amazon.com/dms/latest/APIReference/API_CreateReplicationSubnetGroup.html
        dms_replication_subnet_group = dms.ReplicationSubnetGroup(  # type: ignore[call-arg,misc]
            "DMSReplicationSubnetGroup",
            rp_SubnetIds=[self._public_subnet1.ref(), self._public_subnet2.ref()],
            rp_ReplicationSubnetGroupDescription=f"DMS replication subnet group for {self.env_name}",
            p_ReplicationSubnetGroupIdentifier=f"{self.env_name}-dms-subnet-group",
            ra_DependsOn=[dms_vpc_role],
        )
        group.add(dms_replication_subnet_group)

        dms_security_group_name = f"{self.env_name}-dms-security-group"
        dms_security_group = ec2.SecurityGroup(
            "DMSSecurityGroup",
            rp_GroupDescription=f"DMS security group for {self.env_name}",
            p_GroupName=dms_security_group_name,
            p_VpcId=self._vpc.ref(),
            p_SecurityGroupIngress=[
                ec2.PropSecurityGroupIngress(
                    rp_IpProtocol="-1",
                    p_Description="Allow access from VPC",
                    p_FromPort=-1,
                    p_ToPort=-1,
                    p_CidrIp="10.0.0.0/24",
                ),
                # TODO: Possibly restrict to single provided ClientIP?
                ec2.PropSecurityGroupIngress(
                    rp_IpProtocol="-1",
                    p_Description="Allow access from outside",
                    p_FromPort=-1,
                    p_ToPort=-1,
                    p_CidrIp="0.0.0.0/0",
                ),
            ],
            p_SecurityGroupEgress=[
                ec2.PropSecurityGroupEgress(
                    rp_IpProtocol="-1",
                    p_Description="Allow any access out",
                    p_FromPort=-1,
                    p_ToPort=-1,
                    p_CidrIp="0.0.0.0/0",
                )
            ],
            p_Tags=cf.Tag.make_many(Name=cf.Sub.from_params(dms_security_group_name)),
            ra_DependsOn=[self._vpc, dms_replication_subnet_group],
        )
        group.add(dms_security_group)

        # The replication instance is the main workhorse.
        self._dms_instance = dms.ReplicationInstance(
            "DMSReplicationInstance",
            rp_ReplicationInstanceClass="dms.t3.medium",
            p_ReplicationInstanceIdentifier=f"{self.env_name}-dms-instance",
            p_MultiAZ=False,
            p_ReplicationSubnetGroupIdentifier=dms_replication_subnet_group.ref(),
            p_VpcSecurityGroupIds=[dms_security_group.ref()],
            p_EngineVersion="3.5.2",
            p_AllocatedStorage=5,
            p_PubliclyAccessible=True,
            p_AutoMinorVersionUpgrade=False,
            p_AllowMajorVersionUpgrade=False,
            ra_DependsOn=[
                dms_vpc_role,
                dms_cloudwatch_role,
                dms_security_group,
                dms_replication_subnet_group,
                self._dms_kinesis_access_role,
            ],
        )
        group.add(self._dms_instance)

        # Configuring VPC endpoints as AWS DMS source and target endpoints.
        # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_VPC_Endpoints.html
        vpc_endpoint_stream = ec2.VPCEndpoint(
            "KinesisVPCEndpoint",
            rp_VpcId=self._vpc.ref(),
            rp_ServiceName=f"com.amazonaws.{self.region}.kinesis-streams",
            p_SubnetIds=[self._public_subnet1.ref(), self._public_subnet2.ref()],
            # TODO: Does it really need _both_ security groups?
            p_SecurityGroupIds=[
                self._db_security_group.ref(),
                dms_security_group.ref(),
            ],
            p_VpcEndpointType="Interface",
        )
        group.add(vpc_endpoint_stream)
        return self.add(group)

    def replication(self, dms_table_mapping: t.Dict[str, t.Any]):

        group = cf.ResourceGroup()

        # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.PostgreSQL.html#CHAP_Source.PostgreSQL.Advanced
        # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.PostgreSQL.html#CHAP_Source.PostgreSQL.RDSPostgreSQL
        # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.PostgreSQL.html#CHAP_Source.PostgreSQL.ConnectionAttrib
        source_endpoint = dms.Endpoint(  # type: ignore[call-arg,misc]
            "DMSSourceEndpoint",
            rp_EndpointType="source",
            rp_EngineName="postgres",
            p_ServerName=self._db.rv_EndpointAddress,
            # NOTE: Needs to be integer, so it requires a patched version of cottonformation's `dms` resource wrappers.
            p_Port=self._db.rv_EndpointPort,
            p_SslMode="require",
            p_Username=self.db_username,
            p_Password=self.db_password,
            p_DatabaseName="postgres",
            p_ExtraConnectionAttributes=json.dumps(
                {
                    "CaptureDdls": True,
                    "PluginName": "pglogical",
                }
            ),
            p_EndpointIdentifier=f"{self.env_name}-endpoint-source",
            ra_DependsOn=[self._db],
        )
        target_endpoint = dms.Endpoint(  # type: ignore[call-arg,misc]
            "DMSTargetEndpoint",
            rp_EndpointType="target",
            rp_EngineName="kinesis",
            p_KinesisSettings=dms.PropEndpointKinesisSettings(
                p_StreamArn=self.stream_arn,
                p_MessageFormat="json-unformatted",
                p_IncludeControlDetails=True,
                p_IncludePartitionValue=True,
                p_IncludeTransactionDetails=True,
                p_IncludeNullAndEmpty=True,
                p_IncludeTableAlterOperations=True,
                p_PartitionIncludeSchemaTable=True,
                # The parameter ServiceAccessRoleArn must be provided and must not be blank.
                p_ServiceAccessRoleArn=self._dms_kinesis_access_role.rv_Arn,
            ),
            p_EndpointIdentifier=f"{self.env_name}-endpoint-target",
            ra_DependsOn=[self._stream_source, self._dms_kinesis_access_role],
        )
        group.add(source_endpoint)
        group.add(target_endpoint)

        replication_settings = {
            # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Tasks.CustomizingTasks.TaskSettings.BeforeImage.html
            "BeforeImageSettings": {
                "EnableBeforeImage": True,
                "FieldName": "before-image",
                "ColumnFilter": "pk-only",
            },
            # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Tasks.CustomizingTasks.TaskSettings.Logging.html
            "Logging": {
                "EnableLogging": True,
                "EnableLogContext": True,
                # ERROR: Feature is not accessible.
                # TODO: "LogConfiguration": {"EnableTraceOnError": True},
                "LogComponents": [
                    {"Id": "COMMON", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "ADDONS", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "DATA_STRUCTURE", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "COMMUNICATION", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "FILE_TRANSFER", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "FILE_FACTORY", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "METADATA_MANAGER", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "IO", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "PERFORMANCE", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "SORTER", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "SOURCE_CAPTURE", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "SOURCE_UNLOAD", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "TABLES_MANAGER", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "TARGET_APPLY", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "TARGET_LOAD", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "TASK_MANAGER", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "TRANSFORMATION", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    {"Id": "REST_SERVER", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                    # Replication Settings document error: Unsupported keys were found: VALIDATOR
                    # {"Id": "VALIDATOR", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},  # noqa: ERA001
                    {"Id": "VALIDATOR_EXT", "Severity": "LOGGER_SEVERITY_DETAILED_DEBUG"},
                ],
            },
        }

        """
        replication = dms.ReplicationConfig(  # type: ignore[call-arg,misc]
            "DMSReplicationConfig",
            rp_ReplicationConfigIdentifier=f"{self.env_name}-dms-serverless",
            # p_ResourceIdentifier=f"{self.env_name}-dms-serverless-resource",  # noqa: ERA001
            rp_ReplicationType="full-load-and-cdc",
            rp_SourceEndpointArn=source_endpoint.ref(),
            rp_TargetEndpointArn=target_endpoint.ref(),
            rp_ComputeConfig=dms.PropReplicationConfigComputeConfig(
                rp_MaxCapacityUnits=1,
                p_MinCapacityUnits=1,
                p_MultiAZ=False,
                p_ReplicationSubnetGroupId=dms_replication_subnet_group.ref(),
                p_VpcSecurityGroupIds=[self._db_security_group.ref(), dms_security_group.ref()],
            ),
            rp_TableMappings=map_to_kinesis,
            p_ReplicationSettings=replication_settings,
            ra_DependsOn=[
                dms_replication_subnet_group,
                dms_security_group,
                dms_vpc_role,
                dms_cloudwatch_role,
                dms_target_access_role,
                source_endpoint,
                target_endpoint,
            ],
        )
        group.add(replication)

        replication_config_arn = cf.Output(
            "ReplicationConfigArn",
            Value=replication.rv_ReplicationConfigArn,
        )
        group.add(replication_config_arn)
        return self.add(group)
        """

        replication = dms.ReplicationTask(  # type: ignore[call-arg,misc]
            "DMSReplicationTask",
            # TODO: Use existing replication instance on demand.
            # FIXME: Make configurable.
            rp_ReplicationInstanceArn=self._dms_instance.ref(),
            p_ReplicationTaskIdentifier=f"{self.env_name}-dms-task",
            # p_ResourceIdentifier=f"{self.env_name}-dms-serverless-resource",  # noqa: ERA001
            rp_MigrationType="full-load-and-cdc",
            rp_SourceEndpointArn=source_endpoint.ref(),
            rp_TargetEndpointArn=target_endpoint.ref(),
            # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Tasks.CustomizingTasks.TableMapping.SelectionTransformation.html
            rp_TableMappings=json.dumps(dms_table_mapping),
            # https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Tasks.CustomizingTasks.TaskSettings.html
            p_ReplicationTaskSettings=json.dumps(replication_settings),
            ra_DependsOn=[
                self._dms_instance,
                source_endpoint,
                target_endpoint,
            ],
            ra_DeletionPolicy="Retain",
        )
        group.add(replication)

        replication_task_arn = cf.Output(
            "ReplicationTaskArn",
            Value=replication.ref(),
        )
        group.add(replication_task_arn)

        return self.add(group)

    @property
    def stream_arn(self) -> GetAtt:
        if self._stream_source is None:
            raise ValueError("Kinesis Stream source not defined")
        return self._stream_source.rv_Arn

    def processor(self, factory: LambdaFactory, environment: t.Dict[str, str]):
        """
        Manifest the main processor component of this pipeline.
        """
        self._processor = factory.make(self, environment=environment)
        return self.add(self._processor.group)

    def connect(
        self,
        batch_size: int = 1_000,
        starting_position: t.Literal["LATEST", "TRIM_HORIZON", "AT_TIMESTAMP"] = "TRIM_HORIZON",
        starting_position_timestamp: float = None,
    ):
        """
        Connect the event source to the processor Lambda.

        starting_position:
        - LATEST - Read only new records.
        - TRIM_HORIZON - Process all available records.
        - AT_TIMESTAMP - Specify a time from which to start reading records.

        starting_position_timestamp:
          With `starting_position` set to `AT_TIMESTAMP`, the time from which to start reading,
          in Unix time seconds. `starting_position_timestamp` cannot be in the future.

        https://docs.aws.amazon.com/lambda/latest/dg/services-kinesis-create.html
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html

        aws kinesis register-stream-consumer \
        --consumer-name con1 \
        --stream-arn arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream

        aws lambda create-event-source-mapping \
        --function-name MyFunction \
        --event-source-arn arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream \
        --starting-position LATEST \
        --batch-size 100
        """
        if not self._processor:
            raise RuntimeError("No processor defined")
        if not self._stream_source:
            raise RuntimeError("No Kinesis stream defined")

        # Get a handle to the AWS Lambda for dependency management purposes.
        awsfunc = self._processor.function

        # Create a mapping and add it to the stack.
        mapping = awslambda.EventSourceMapping(
            id="KinesisToLambdaMapping",
            rp_FunctionName=awsfunc.p_FunctionName,
            p_EventSourceArn=self._stream_source.rv_Arn,
            p_BatchSize=batch_size,
            p_StartingPosition=starting_position,
            p_StartingPositionTimestamp=starting_position_timestamp,
            ra_DependsOn=awsfunc,
        )
        return self.add(mapping)
