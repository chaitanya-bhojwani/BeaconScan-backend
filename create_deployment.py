import os
import subprocess
import zipfile
import glob
import datetime
import sys
import argparse

"""
Script will create an AWS Lambda function deployment.

It expects there to be a deployments directory and it will create a
deployment of the form:

deployment_n

where n is incremented for each deployment based on the existing deployment
directories

optional argument
if pass with --deploy and functionname, it will deploy the lambda
if pass with --profile and profilename, it will deploy using AWS credential configured with profilename

"""

root_deployments_dir = "./deployments"

# List of files that should be included in the deployment
# Only the files listed here, and the libraries in the requirements.txt
# file will be included in the deployment.
 
deployment_files = (glob.glob("lambda_function.py"))
dir_not_to_include = [".git", "deployments"]


def _read_requirements():
    with open("./requirements.txt", 'r') as f:
        install_requirements = f.readlines()

    return install_requirements





def _make_deployment_dir():
    deployment_name = "deployment_{0}".format(datetime.datetime.today().strftime('%Y-%m-%d_%H:%M:%S'))
    new_deployment_dir_path = "{0}/{1}".format(root_deployments_dir, deployment_name)

    if not os.path.exists(new_deployment_dir_path):
        os.mkdir(new_deployment_dir_path)

    return (new_deployment_dir_path, deployment_name)


def _install_requirements(deployment_requirements, deployment_dir):
    """
    pip install <requirements line> -t <deployment_dir>
    :param deployment_requirements
    :param deployment_dir:
    :return:
    """
    if os.path.exists(deployment_dir):
        for requirement in deployment_requirements:
            cmd = "pip install --upgrade {0} -t {1}".format(requirement, deployment_dir).split()
            return_code = subprocess.call(cmd, shell=False)


def _copy_deployment_files(deployment_dir):
    for deployment_file in deployment_files:
        if os.path.exists(deployment_file):
            cmd = "cp {0} {1}".format(deployment_file, deployment_dir).split()
            return_code = subprocess.call(cmd, shell=False)
        else:
            raise NameError("Deployment file not found [{0}]".format(deployment_file))
    
def _copy_dependent_dir(deployment_dir):
    #copying all the directory
    dir_to_include = [f for f in os.listdir(".") if os.path.isfile(f) == False]
    for d in dir_not_to_include:
        if d in dir_to_include:
            dir_to_include.remove(d)


    for dependent_dir in dir_to_include:
        if os.path.exists(dependent_dir):
            cmd = "cp -r {0} {1}".format(dependent_dir, deployment_dir).split()
            return_code = subprocess.call(cmd, shell=False)
        else:
            raise NameError("Deployment file not found [{0}]".format(deployment_file))

def zipdir(dirPath=None, zipFilePath=None, includeDirInZip=False):
    """
    Attribution:  I wish I could remember where I found this on the
    web.  To the unknown sharer of knowledge - thank you.

    Create a zip archive from a directory.

    Note that this function is designed to put files in the zip archive with
    either no parent directory or just one parent directory, so it will trim any
    leading directories in the filesystem paths and not include them inside the
    zip archive paths. This is generally the case when you want to just take a
    directory and make it into a zip file that can be extracted in different
    locations.

    Keyword arguments:

    dirPath -- string path to the directory to archive. This is the only
    required argument. It can be absolute or relative, but only one or zero
    leading directories will be included in the zip archive.

    zipFilePath -- string path to the output zip file. This can be an absolute
    or relative path. If the zip file already exists, it will be updated. If
    not, it will be created. If you want to replace it from scratch, delete it
    prior to calling this function. (default is computed as dirPath + ".zip")

    includeDirInZip -- boolean indicating whether the top level directory should
    be included in the archive or omitted. (default True)

"""
    if not zipFilePath:
        zipFilePath = dirPath + ".zip"
    if not os.path.isdir(dirPath):
        raise OSError("dirPath argument must point to a directory. '%s' does not." % dirPath)
    parentDir, dirToZip = os.path.split(dirPath)

    # Little nested function to prepare the proper archive path

    def trimPath(path):
        archivePath = path.replace(parentDir, "", 1)
        if parentDir:
            archivePath = archivePath.replace(os.path.sep, "", 1)
        if not includeDirInZip:
            archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
        return os.path.normcase(archivePath)

    outFile = zipfile.ZipFile(zipFilePath, "w", compression=zipfile.ZIP_DEFLATED)
    for (archiveDirPath, dirNames, fileNames) in os.walk(dirPath):
        for fileName in fileNames:
            filePath = os.path.join(archiveDirPath, fileName)
            outFile.write(filePath, trimPath(filePath))
        # Make sure we get empty directories as well
        if not fileNames and not dirNames:
            zipInfo = zipfile.ZipInfo(trimPath(archiveDirPath) + "/")
            # some web sites suggest doing
            # zipInfo.external_attr = 16
            # or
            # zipInfo.external_attr = 48
            # Here to allow for inserting an empty directory.  Still TBD/TODO.
            outFile.writestr(zipInfo, "")
    outFile.close()

    
def deployLambda(zip_file, lambda_name, profile_name):
    #CMD = "aws lambda update-function-code --function-name alpr_license_plate --zip-file fileb://deployments/deployment_2018-04-13_11\:30\:02.zip  --profile=pq"
    CMD = "aws lambda update-function-code --function-name %s --zip-file fileb://'%s' "%(lambda_name, zip_file)
    if profile_name is not None:
        CMD = CMD + " --profile=%s"%profile_name

    print("\n\n\nUploading lambda........\n")
    print(subprocess.Popen(CMD, stdout=subprocess.PIPE, shell=True).stdout.read())


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--deploy ',nargs='?', type=str, dest='deploy',help='If functioname is provided, script will\
            be deployed to the given lambda function')
    parser.add_argument('--profile ',nargs='?', type=str, dest='profile', help='If profile is provided, aws will use\
            credential for given profile else use default credential')

    args = parser.parse_args()
    
    
    (deployment_dir, deployment_name) = _make_deployment_dir()
    _copy_deployment_files(deployment_dir)
    _copy_dependent_dir(deployment_dir)
    install_requirements = _read_requirements()
    _install_requirements(install_requirements, deployment_dir)

    deployment_zip_file = "{0}/{1}.zip".format(root_deployments_dir, deployment_name)
    zipdir(deployment_dir, deployment_zip_file)

    if args.deploy is not None:
        deployLambda(deployment_zip_file.replace("./",""),args.deploy, args.profile)
