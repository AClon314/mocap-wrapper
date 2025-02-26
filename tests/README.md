# Python Project Template
This is a Python project template that anyone can use with basic CI/CD pipeline, issue and PR templates etc.

## Directory Structure
You can remove the `(optional)` directories if you don't need them. (e.g. `docker/`, `setup.py`, etc.)
```
python-project-template/    
├── .github/                # GA workflows & PR, Issue templates
├── docker/                 # (optional) Dockerfile & docker-compose files related to the project.  
├── tests/                  # Test codes with pytest
├── .gitignore              # gitignore file 
├── README.md               # README file
├── pyproject.toml          # (optional) PyPI package configuration file
├── setup.py                # (optional) PyPI package setup file
└── requirements.txt        # Project dependencies 
```

## Github Actions
1. [ci.yml](https://github.com/jhj0517/python-project-template/tree/master/.github/workflows/ci.yml)

Basic CI workflow with pytest. It runs tests in the [tests/](https://github.com/jhj0517/python-project-template/tree/master/tests) directory, with master branch commit & PR triggers by default.

2. [publish-dockerhub.yml](https://github.com/jhj0517/python-project-template/tree/master/.github/workflows/publish-dockerhub.yml)

Basic CD workflow for DockerHub publishing. You can remove this workflow if you don't need it.<br>
It will build the docker image with files in the [docker/](https://github.com/jhj0517/python-project-template/tree/master/docker) and publish it to the dockerhub. The auto-trigger of the action is disabled by default.<br>
Before using the workflow, you need to set the `DOCKER_USERNAME ` & `DOCKER_PASSWORD` in the repository settings.

![image](https://github.com/user-attachments/assets/ab9f7081-fa07-4181-af30-b6646161bc0b)

And make sure to edit the `image-name` in the workflow.

https://github.com/jhj0517/python-project-template/blob/0c9dc95cece122815f1096607b952b1a033e2e7d/.github/workflows/publish-dockerhub.yml#L43-L44


3. [publish-pypi.yml](https://github.com/jhj0517/python-project-template/tree/master/.github/workflows/publish-dockerhub.yml)
   
Basic CD workflow for pypi package. You can remove this workflow if you don't need it. <br>
The auto-trigger for this workflow is disabled by default. If enabled, it will build and publish to pypi whenever you make a new "release" in the repository.  

Before using the workflow, edit package name to yours in the workflow.

https://github.com/jhj0517/python-project-template/blob/0c9dc95cece122815f1096607b952b1a033e2e7d/.github/workflows/publish-pypi.yml#L18-L19

## Issue & PR Template
There are some basic templates for the issue & PR. You can edit them or add more to fit your project's needs.

- Issue Templates:
  1. [bug_report.md](https://github.com/jhj0517/python-project-template/tree/master/.github/ISSUE_TEMPLATE/bug_report.md) : Basic bug report template
  2. [feature_request.md](https://github.com/jhj0517/python-project-template/tree/master/.github/ISSUE_TEMPLATE/feature_request.md) : Feature request template

- PR Template: [pull_request_template.md](https://github.com/jhj0517/python-project-template/tree/master/.github/pull_request_template.md)


## Docker

The [docker/](https://github.com/jhj0517/python-project-template/tree/master/docker) directory and [publish-dockerhub.yml](https://github.com/jhj0517/python-project-template/tree/master/.github/workflows/publish-dockerhub.yml) are associated with the Docker CI/CD pipeline. You can remove them if you don't need them.

Before building image, make sure to edit the variable in the [docker/Dockerfile](https://github.com/jhj0517/python-project-template/tree/master/docker/Dockerfile):

https://github.com/jhj0517/python-project-template/blob/0c9dc95cece122815f1096607b952b1a033e2e7d/docker/Dockerfile#L3-L4

And edit [docker/docker-compose.yaml](https://github.com/jhj0517/python-project-template/tree/master/docker/docker-compose.yaml) as well:

https://github.com/jhj0517/python-project-template/blob/0c9dc95cece122815f1096607b952b1a033e2e7d/docker/docker-compose.yaml#L6-L7

The image is built and published automatically by the CI/CD pipeline, but you can also manually build and run the image with the following commands.

1. git clone this repository
```bash
git clone https://github.com/your-name/your-project-name.git
```
2. Build the image
```bash
docker compose -f docker/docker-compose.yaml build
```
3. Run the container
```bash
docker compose -f docker/docker-compose.yaml up
```

## PyPI
The [setup.py](https://github.com/jhj0517/python-project-template/tree/master/setup.py), [pyproject.toml](https://github.com/jhj0517/python-project-template/tree/master/pyproject.toml) and [publish-pypi.yml](https://github.com/jhj0517/python-project-template/tree/master/.github/workflows/publish-dockerhub.yml) are associated with the PyPI package CI/CD pipeline. You can remove them if you don't need them.

Make sure to edit dependencies & variables in the [pyproject.toml](https://github.com/jhj0517/python-project-template/tree/master/pyproject.toml) as your project's needs.

## How to start 
Click "Use this template" and "Create a new repository". Then you can start your own project with `git clone`. 

![image](https://github.com/user-attachments/assets/b628232a-09b1-4f49-9751-5ec4723d60ab)

