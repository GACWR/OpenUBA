# OpenUBA (Open User Behavior Analytics)
A robust, and flexible open source User & Entity Behavior Analytics (UEBA) framework used for Security Analytics. Developed with luv by Data Scientists & Security Analysts from the Cyber Security Industry.

*This project is a work in progress and in a pre-alpha state; input and contributions are warmly welcome*

| Status Type | Status |
| --- | --- |
| `Master Build` | [![Build Status](https://travis-ci.org/GACWR/OpenUBA.svg?branch=master)](https://travis-ci.org/GACWR/OpenUBA) |
| `Development Build` | [![Build Status](https://travis-ci.org/GACWR/OpenUBA.svg?branch=main_dev_branch)](https://travis-ci.org/GACWR/OpenUBA) |
| `Issues` | [![Issues](https://img.shields.io/github/issues/GACWR/OpenUBA.svg)](https://github.com/GACWR/OpenUBA/issues) |
| `Closed Issues` | [![GitHub issues-closed](https://img.shields.io/github/issues-closed/GACWR/OpenUBA.svg)](https://GitHub.com/GACWR/OpenUBA/issues?q=is%3Aissue+is%3Aclosed) |
| `Last Commit` | [![Last commit](https://img.shields.io/github/last-commit/GACWR/OpenUBA.svg)](https://github.com/GACWR/OpenUBA/commits/master) |
| `UI Docker Stars` | [![Docker Stars](https://img.shields.io/docker/stars/gacwr/openuba-ui.svg)](https://hub.docker.com/r/gacwr/openuba-ui) |
| `UI Docker Pulls` | [![Docker Pulls](https://img.shields.io/docker/pulls/gacwr/openuba-ui.svg)](https://hub.docker.com/r/gacwr/openuba-ui) |
| `UI Docker Automated` | [![Docker Automated](https://img.shields.io/docker/cloud/automated/gacwr/openuba-ui.svg)](https://hub.docker.com/r/gacwr/openuba-ui) |
| `UI Docker Build` | [![Docker Build](https://img.shields.io/docker/cloud/build/gacwr/openuba-ui.svg)](https://hub.docker.com/r/gacwr/openuba-ui) |
| `Server Docker Stars` | [![Docker Stars](https://img.shields.io/docker/stars/gacwr/openuba-server.svg)](https://hub.docker.com/r/gacwr/openuba-server) |
| `Server Docker Pulls` | [![Docker Pulls](https://img.shields.io/docker/pulls/gacwr/openuba-server.svg)](https://hub.docker.com/r/gacwr/openuba-server) |
| `Server Docker Automated` | [![Docker Automated](https://img.shields.io/docker/cloud/automated/gacwr/openuba-server.svg)](https://hub.docker.com/r/gacwr/openuba-server) |
| `Server Docker Build` | [![Docker Build](https://img.shields.io/docker/cloud/build/gacwr/openuba-server.svg)](https://hub.docker.com/r/gacwr/openuba-server) |
| `License` | [![License](https://img.shields.io/badge/license-GPL-blue.svg)](https://github.com/GACWR/OpenUBA/blob/master/LICENSE) |
| `Releases` | [![Downloads](https://img.shields.io/github/downloads/GACWR/OpenUBA/total.svg)](https://github.com/GACWR/OpenUBA/releases) |
| `Latest Release` | [![Downloads](https://img.shields.io/github/downloads/GACWR/OpenUBA/total.svg)](https://github.com/GACWR/OpenUBA/releases) |
| `Top Language` | [![Top language](https://img.shields.io/github/languages/top/GACWR/OpenUBA.svg)](https://github.com/GACWR/OpenUBA) |
| `Code Size` | [![Code size in bytes](https://img.shields.io/github/languages/code-size/GACWR/OpenUBA.svg)](https://github.com/GACWR/OpenUBA) |
| `Chat` | ![Discord](https://img.shields.io/discord/683561405928177737) |

## Architecture
<img src="images/framework.jpg" width="750px" />


## Goals
To Build a lightweight, SIEM Agnostic, UEBA Framework focused on providing:
- Modeling
  - Model Management
  - Community-driven Model Library
  - Model Version Control
  - Ready-to-use model modules
  - Feedback Loop for continuous model training
  - "Shadow Mode" for model and risk score experimentation
  - Simple model configuration workflow
  - Model groups
  - Single-fire & Sequential models
- Dashboard
  - Modern stack
  - Modular components
  - Live updating
  - Global state, and component state
- Features
  - Rule Storage/Management
  - Case Management
  - Peer-oriented/community intel
  - Lightweight, SIEM-agnostic architecture
  - Flexible/open dataset support
  - Alerting/Ticketing system
  - Browser & desktop applications

## Stack
- Client Dashboard
  - React
  - Bootstrap
  - Node JS
  - Express JS
  - D3.js
- Model Server (Remote or Local)
- API Server
  - Flask
- Visualization
  - Data Shader
  - Kibana
  - Matplotlib
  - NetworkX
- Modeling
  - Tensorflow
  - Scikit Learn
  - Keras
  - GP Learn
  - DEAP
  - Graphx
  - MLlib
- Compute Engine
  - Spark
  - Elastic Search
- Supported Data Formats (for now)
  - CSV
  - Parquet
  - Flat File


# User Interface (placeholder, UI being updated now)
<img src="images/ui.png" width="750px" />

The interface is meant to observe system events, and anomalies


## Views
- Dashboard (index)
- Anomalies
- Cases
- Modeling
- Settings

# Model Library
OpenUBA implements a model library purposed with hosting ready-to-use models, both developed by us, and the community. For starters, we host the default model repository, similar to any popular package manager (npm, cargo, etc). However, developers can host their own model repository for use in their own instance of OpenUBA.

Model installation currently works as follows:
<img src="images/model_library_workflow.png" width="750px" />


## Installation/Usage
Go to [INSTALL.md](https://github.com/GACWR/OpenUBA/blob/master/docs/INSTALL.md)


## Get the updated code & documentation on XS code [here](https://cp.xscode.com/GACWR/OpenUBA)
Our main development, and documentation branches are first pushed to our sponsorship repository, and then eventually pushed to our public free repository. To obtain the most updated code, and documentation for OpenUBA, subscribe to our XS Code repository.


## Discord (Main Server, and Dev Chat)
Discord Server: https://discord.gg/Ps9p9Wy

## Telegram (Backup server, other communications)
Telegram: https://t.me/GACWR
