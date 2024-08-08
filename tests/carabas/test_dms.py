def test_endpoint_port_integer():
    """
    Verify p_Port is defined as an integer.

    TODO: Does not perform the validation yet. How?
    """
    from lorrystream.carabas.aws.cf.dms_next import Endpoint

    ep = Endpoint("foobar", rp_EndpointType="foo", rp_EngineName="bar")
    assert hasattr(ep, "p_Port")
