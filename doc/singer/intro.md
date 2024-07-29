## About

An introduction to the Singer ecosystem of data pipeline components for
composable open source ETL.

Singer, Meltano, PipelineWise, and Airbyte, provide components and integration
engines adhering to the Singer specification.

On the database integration side, the [connectors] of Singer and Meltano are
based on [SQLAlchemy].

https://en.wikipedia.org/wiki/Data_integration


## Overview

### Stitch
_Developers shouldn't have to write ETL scripts._

> Consolidate your data in minutes. No API maintenance, scripting, cron jobs,
> or JSON wrangling required. Set up in minutes unlimited data volume during
> trial 5 million rows of data free, forever.

> “With Stitch, we were able to get our data streaming to our warehouse in
> minutes; and it requires zero engineering maintenance.”

Stitch is a cloud-first, developer-focused platform for rapidly moving data.
Stitch was acquired by Talend in November 2018 and operates as an independent
business unit.

- [Stich @ 2017]
- https://www.stitchdata.com/
- https://github.com/stitchdata
- https://www.stitchdata.com/company/
- https://www.talend.com/products/data-loader/

### Singer
_The open-source standard for writing scripts that move data._

[Singer] is an open source specification and software framework for [ETL]/[ELT]
data exchange between a range of different systems. For talking to SQL databases,
it employs a metadata subsystem based on SQLAlchemy.

Singer reads and writes Singer-formatted JSONL messages, following the [Singer Spec].

> The Singer specification was started in 2016 by Stitch Data. It specified a
> data transfer format that would allow any number of data systems, called taps,
> to send data to any data destinations, called targets. Airbyte was incorporated
> in 2020 and created their own specification that was heavily inspired by Singer.
> There are differences, but the core of each specification is sending new-line
> delimited JSON data from STDOUT of a tap to STDIN of a target.

### PipelineWise
> [PipelineWise] is another Data Pipeline Framework using the Singer.io
specification to ingest and replicate data from various sources to
various destinations. The list of [PipelineWise Taps] include another
bunch of high-quality data-source and -sink components.

### Data Mill
> Data Mill helps organizations utilize modern data infrastructure and data
> science to power analytics, products, and services.

- https://github.com/datamill-co
- https://datamill.co/

### Meltano
_Unlock all the data that powers your data platform._

> _Say goodbye to writing, maintaining, and scaling your own API integrations
with Meltano's declarative code-first data integration engine, bringing
a number of APIs and DBs to the table._

[Meltano] builds upon Singer technologies, uses configuration files in YAML
syntax instead of JSON, adds an improved SDK and other components, and runs
the central addon registry, [meltano | Hub].

### dbt
data build tool (dbt) is an open-source command line tool that helps analysts
and engineers transform data in their warehouse more effectively.

- https://en.wikipedia.org/wiki/Data_build_tool

#### History
It started at [RJMetrics] in 2016 as a solution to add basic transformation
capabilities to Stitch (acquired by Talend in 2018). The earliest versions
of dbt allowed analysts to contribute to the data transformation process
following the best practices of software engineering.

### Estuary
_MEET THE FASTEST, MOST RELIABLE ETL._

> The only platform built from the ground up for truly real-time ETL and ELT
> data integration, set up in minutes.

#### Captures
- Captures extract data from an endpoint using a connectors.
- Estuary builds and maintains many real-time connectors for various
  technology systems, such as database change data capture (CDC) connectors.
- Captures run continuously: As soon as new documents are made available at
  the endpoint resources, Flow validates their schema and adds them to the
  appropriate collection. Captures can process documents up to 16 MB in size.

#### Batch sources
Flow supports running both first and third party connectors to batch sources
including Singer, Meltano and Airbyte as well as natively-written Estuary
connectors. These connectors tend to focus on SaaS APIs, and do not offer
real-time streaming integrations. Flow runs the connector at regular intervals
to capture updated documents.

- https://estuary.dev/
- https://estuary.dev/integrations/
- https://github.com/estuary/flow
- https://github.com/estuary/connectors

### Qlik
> Make better use of enterprise assets. With Qlik Talend® Data Integration
> and Quality you can drive AI innovation, intelligent decisions, and
> business modernization.

> Stitch can replicate data from all your sources to a central warehouse.
> From there, it's easy to use Qlik to perform the in-depth analysis you need.

> Accelerate data replication, ingestion and streaming across a wide variety
> of heterogeneous databases, data warehouses, and big data platforms. You’ll
> be able to move your data easily, securely and efficiently with minimal
> operational impact.

In 2023, Qlik acquired Talend.

- https://en.wikipedia.org/wiki/Qlik
- https://www.qlik.com/us/products/qlik-replicate
- https://www.stitchdata.com/analysis-tools/qlik/
- https://www.qlik.com/us/products/stitch-data-loader
- https://community.qlik.com/t5/Stitch/A-new-board-to-talk-about-all-things-Stitch/td-p/2404246

### Omni Analytics
_All jobs are data jobs._

> Business intelligence that speaks your language
> Explore, visualize, and model data your way with Omni.
> From spreadsheets to SQL—in a single platform.

> Data tool proliferation has gone off-the-rails. There’s now
> a tool for every data need, but they all require compromises.

Founded in 2022. [RJMetrics alum Chris Merrick is behind Omni].

-- https://omni.co/


## Evaluations

### Singer vs. Meltano

Meltano as a framework fills many gaps and makes Singer convenient to actually
use. It is impossible to outline all details and every difference, so we will
focus on the "naming things" aspects for now.

Both ecosystems use different names for the same elements. That may be confusing
at first, but it is easy to learn: For the notion of **data source** vs. **data
sink**, common to all pipeline systems in one way or another, Singer uses the
terms **tap** vs. **target**, while Meltano uses **extractor** vs. **loader**.
Essentially, they are the same things under different names.

| Ecosystem | Data source | Data sink |
|--------|--------|--------|
| Singer | Tap | Target |
| Meltano | Extractor | Loader |

In Singer jargon, you **tap** data from a source, and send it to a **target**.
In Meltano jargon, you **extract** data from a source, and then **load** it
into the target system.


### Singer and Airbyte criticism

- https://airbyte.com/etl-tools/singer-alternative-airbyte
- https://airbyte.com/blog/airbyte-vs-singer-why-airbyte-is-not-built-on-top-of-singer
- https://airbyte.com/blog/why-you-should-not-build-your-data-pipeline-on-top-of-singer
- https://airbyte.com/blog/a-new-license-to-future-proof-the-commoditization-of-data-integration
- [Clarify in docs relationship to Singer project from Stitch/Talend]
- [Unfair comparison to PipelineWise and Meltano]


## Timeline

### June 2, 2016
- [Paul Singer to cash in on $3B takeover of Qlik Technologies]
- [Thoma Bravo to buy analytics firm Qlik]

### Oct 26, 2016
Christopher Merrick submits first commit on Stitch.
https://github.com/stitchdata/python-stitch-client/commit/bcc84f232

### Oct 28, 2016
Christopher Merrick submits first commit of the Python Singer implementation.
https://github.com/singer-io/singer-python/commit/64990dd0ae

### Nov 17, 2016
Christopher Merrick submits first commit of the Singer specification.
https://github.com/singer-io/getting-started/commit/f780adab0

### November 7, 2018
[Talend to Acquire Stitch], a leader in self-service Cloud data integration.

### June 30, 2021
[GitLab spins out open source data integration platform Meltano]

### October 6, 2021
[Estuary helps enterprises harness historical and real-time data pipelines]

### August 16, 2022
[Introducing Omni], the new generation of business intelligence, founded
by Chris Merrick, Colin Zima, and Jamie Davidson.

### May 16, 2023
[Qlik Acquires Talend], combining its Best-in-Class Data Integration with
Talend’s Leading Data Transformation, Quality, and Governance Capabilities.
Talend and Qlik's Data Integration and Quality solutions automate the delivery
of trusted, business-ready data, enabling smarter decisions, operational
efficiency, and innovation. 

### May 24, 2024
> The co-founders of Omni Analytics, CEO Colin Zima, President Jamie Davidson,
> and CTO Christopher Merrick have spent a decade building data products,
> such as Looker and Stitch. They bring a wealth of experience in business
> intelligence, semantic layers, cloud data management, and customer-first support.
>
> - [Snowflake: Snowflake Ventures Invests in Omni]
> - [Omni: Snowflake Ventures invests in Omni]

## Comparisons
- [Fivetran vs. Stitch vs. Singer vs. Airbyte vs. Meltano]
- [Top 7 ELT tools in 2024]
- [Portable: ETL Connector Catalog]
- [Rivery vs. Stitch Data]
  - https://community.rivery.io/

[Clarify in docs relationship to Singer project from Stitch/Talend]: https://github.com/airbytehq/airbyte/issues/445
[connectors]: https://hub.meltano.com/
[ELT]: https://en.wikipedia.org/wiki/Extract,_load,_transform
[ETL]: https://en.wikipedia.org/wiki/Extract,_transform,_load
[Estuary helps enterprises harness historical and real-time data pipelines]: https://venturebeat.com/business/how-estuary-helps-enterprises-harness-historical-and-real-time-data-pipelines/
[Fivetran vs. Stitch vs. Singer vs. Airbyte vs. Meltano]: https://www.reddit.com/r/dataengineering/comments/o744oi/fivetan_vs_stitch_vs_singer_vs_airbyte_vs_meltano/
[GitLab spins out open source data integration platform Meltano]: https://venturebeat.com/business/gitlab-spins-out-open-source-data-integration-platform-meltano/
[Introducing Omni]: https://omni.co/blog/introducing-omni
[Meltano]: https://meltano.com/
[meltano | Hub]: https://hub.meltano.com/
[Meltano SDK]: https://github.com/meltano/sdk
[Meltano PostgreSQL target]: https://pypi.org/project/meltanolabs-target-postgres/
[Omni: Snowflake Ventures invests in Omni]: https://omni.co/blog/snowflake-invests-in-omni
[Paul Singer to cash in on $3B takeover of Qlik Technologies]: https://nypost.com/2016/06/02/paul-singer-to-cash-in-on-3b-takeover-of-qlik-technologies/
[PipelineWise]: https://transferwise.github.io/pipelinewise/
[PipelineWise Taps]: https://transferwise.github.io/pipelinewise/user_guide/yaml_config.html
[Portable: ETL Connector Catalog]: https://portable.io/connectors
[Qlik Acquires Talend]: https://www.qlik.com/us/company/press-room/press-releases/qlik-acquires-talend
[Rivery vs. Stitch Data]: https://portable.io/learn/rivery-vs-stitch-comparison
[RJMetrics]: https://en.wikipedia.org/wiki/RJMetrics
[RJMetrics alum Chris Merrick is behind Omni]: https://technical.ly/startups/omni-chris-merrick-data-philly/
[Singer]: https://www.singer.io/
[Singer Spec]: https://hub.meltano.com/singer/spec/
[Snowflake: Snowflake Ventures Invests in Omni]: https://www.snowflake.com/blog/snowflake-ventures-invests-in-omni-to-empower-self-service-business-intelligence-and-data-modeling/
[SQLAlchemy]: https://www.sqlalchemy.org/
[Stich @ 2017]: https://web.archive.org/web/20170130075831/https://www.stitchdata.com/
[Talend to Acquire Stitch]: https://www.talend.com/about-us/press-releases/talend-acquires-stitch-a-leader-in-self-service-cloud-data-integration/
[Thoma Bravo to buy analytics firm Qlik]: https://www.reuters.com/article/us-qlik-m-a-thoma-bravo-idUSKCN0YO1JD/
[Top 7 ELT tools in 2024]: https://portable.io/learn/top-5-elt-tools-for-your-modern-data-stack
[Unfair comparison to PipelineWise and Meltano]: https://github.com/airbytehq/airbyte/issues/9253
