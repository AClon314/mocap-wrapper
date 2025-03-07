from setuptools import setup, find_packages

if __name__ == '__main__':
    setup(
        packages=find_packages(include=['mocap_wrapper', 'mocap_wrapper.*']),
    )
