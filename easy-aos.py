#!/bin/env python2

from __future__ import print_function

import os, sys, re, time
import signal
import pipes
from subprocess import check_call,check_output,CalledProcessError,STDOUT
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser, Namespace
from datetime import datetime

try:
    from termcolor import cprint
except ImportError:
    print('No termcolor module found,please download "termcolor.py" file from same place!')
    yes = raw_input('Download "termcolor.py" under current dir? [y/n]: ')
    if 'y' == yes.lower():
        dstFile = raw_input('input the URL of file: ')
        check_output('wget {}'.format(dstFile), shell=True)
        print('\033[1;31m[IMPORTANT] Please copy it to the same directory as "easy-aos.py"!!! [IMPORTANT]\033[0m')
        os.sys.exit(1)
    else:
       print("Note: The default color will be used for output messages.")
       cprint = print

config = SafeConfigParser()

# Show friendly messages when Ctrl+C to terminate
def signal_handler(signal, frame):
    cprint('\nStopped by Ctrl+C!','red')
    sys.exit(1)

class AOS(object):
    '''Make easier for OpenShift tests!'''

    osConfigFile = "./aos.conf"
    osUser=""
    osPasswd=""
    osUserToken=""
    masterUser=""
    master=""
    masterConfigRoot=""
    masterConfigFile=""
    kubeConfigFile=""
    pemFile=""
    hawkularMetricsAppname=""
    kibanaOpsAppname=""
    kibanaAppname=""
    SAMetricsDeployer=""
    HCHStack=""
    imagePrefix=""
    imageVersion=""
    enablePV=""
    enableKibanaOps=""
    ESRam=""
    ESClusterSize=1
    PVCSize = 0
    cassandraNodes = 1
    EFKDeployer=""
    RegistryQEToken = ""
    TokenUser = ""
    TokenUserEMail = ""
    deployMode = ""
    useJournal = ""
    userWriteAccess = ""
    dynamicallyPV = ""
    lbHost = ""
    masterPort = "8443"

    SSHIntoMaster=""
    ScpFileFromMaster=""
    osProject=""
    delProject = False
    pullLoggingMetricsImage = False
    isOSEServer = False
    MasterURL = ""
 
    ocWithPathOnMaster = ""
    oadmWithPathOnMaster = ""

    # Create the default configration file
    @staticmethod
    def generate_default_config():
        '''Create the default config file if not exists'''

        config.add_section("global")
        config.add_section("metrics")
        config.add_section("logging")
        config.add_section("component_shared")
        config.add_section("ssh")
        config.set('global','lb_host','')
        config.set('global','# The OpenShift user','')
        config.set('global','os_user','')
        config.set('global',"# The OpenShift user's password",'')
        config.set('global','os_passwd','')
        config.set('global',"# The OpenShift user's token",'')
        config.set('global','os_user_token','')
        config.set('global','# The master host user','')
        config.set('global','master_user','root')
        config.set('global','# The master DNS name','')
        config.set('global','master','')
        config.set('global','master_config_root','/etc/origin/master')
        config.set('global','master_config_file','master-config.yaml')
        config.set('global','kube_config_file','admin.kubeconfig')
        config.set('ssh','# The pem file for ssh into master host','')
        config.set('ssh','pem_file','')
        config.set('metrics','# Map to metrics parameter DYNAMICALLY_PROVISION_STORAGE','')
        config.set('metrics','dynamically_provision_storage','true')
        config.set('metrics','# Map to metrics parameter HAWKULAR_METRICS_HOSTNAME','')
        config.set('metrics','hawkular_metrics_appname','hawkular-metrics')
        config.set('logging','# Map to logging parameter kibana-ops-hostname','')
        config.set('logging','kibana_ops_appname','kibana-ops')
        config.set('logging','# Map to logging parameter enable-ops-cluster','')
        config.set('logging','enable_kibana_ops','true')
        config.set('logging','# Map to logging parameter kibana-hostname','')
        config.set('logging','kibana_appname','kibana')
        config.set('metrics','# The metrics deployer serviceaccount template json file','')
        config.set('metrics','serviceaccount_metrics_deployer','https://raw.githubusercontent.com/openshift/origin-metrics/master/metrics-deployer-setup.yaml')
        config.set('metrics','# The metrics deployer template json file','')
        config.set('metrics','hch_stack','https://raw.githubusercontent.com/openshift/origin-metrics/master/metrics.yaml')
        config.set('component_shared','image_prefix','openshift/origin-')
        config.set('component_shared','#image_prefix0','registry.qe.openshift.com/openshift3/')
        config.set('component_shared','#image_prefix1','brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888/openshift3/')
        config.set('component_shared','#image_prefix2','brew-pulp-docker01.web.qa.ext.phx1.redhat.com:8888/openshift3/')
        config.set('component_shared','#image_prefix3','registry.ops.openshift.com/openshift3/')
        config.set('component_shared','image_version','latest')
        config.set('component_shared','enable_pv','true')
        config.set('logging','elastic_ram','1G')
        config.set('logging','elastic_cluster_size','1')
        config.set('component_shared', 'pvc_size', '10')
        config.set('component_shared', 'registryqe_token','')
        config.set('component_shared', 'token_user', 'chunchen')
        config.set('component_shared', 'deploy_mode', 'deploy')
        config.set('component_shared', 'token_user_email', 'chunchen@redhat.com')
        config.set('logging','efk_deployer','https://raw.githubusercontent.com/openshift/origin-aggregated-logging/master/deployer/deployer.yaml')
        config.set('metrics', 'Map to metrics parameter CASSANDRA_NODES','')
        config.set('metrics', 'cassandra_nodes','2')
        config.set('logging','# Map to logging parameter use-journal','')
        config.set('logging', 'use_journal', 'false')
        config.set('metrics','# Map to metrics parameter USER_WRITE_ACCESS','')
        config.set('metrics', 'user_write_access', 'false')

        with open(AOS.osConfigFile, 'wb') as defaultconfig:
           config.write(defaultconfig)

        cmd = "sed -i 's/^#\(.*\)=/#\\1/g' {}".format("./aos.conf")
        AOS.run_ssh_command(cmd,ssh=False)

    @staticmethod
    def show_current_config():
        config.read(AOS.osConfigFile)
        for section in config.sections():
            items = config.items(section)
            items_with_newline = '\n'.join([' = '.join(item) for item in items])
            cprint('\n['+section+']', 'green')
            cprint(items_with_newline, 'blue')

    @staticmethod
    def get_config(args):
        config.read(AOS.osConfigFile)
        AOS.lbHost = config.get("global","lb_host")
        AOS.osUser = config.get("global","os_user")
        AOS.osPasswd = config.get("global","os_passwd")
        AOS.osUserToken = config.get("global", "os_user_token")
        AOS.masterUser = config.get("global","master_user")
        AOS.master = config.get("global","master")
        AOS.masterConfigRoot = config.get("global","master_config_root")
        AOS.masterConfigFile = config.get("global","master_config_file")
        AOS.kubeConfigFile = config.get("global","kube_config_file")
        AOS.pemFile = config.get("ssh","pem_file")
        AOS.hawkularMetricsAppname = config.get("metrics","hawkular_metrics_appname")
        AOS.kibanaOpsAppname = config.get("logging","kibana_ops_appname")
        AOS.kibanaAppname = config.get("logging","kibana_appname")
        AOS.SAMetricsDeployer = config.get("metrics","serviceaccount_metrics_deployer")
        AOS.HCHStack = config.get("metrics","hch_stack")
        AOS.imagePrefix = config.get("component_shared","image_prefix")
        AOS.imageVersion = config.get("component_shared","image_version")
        AOS.enablePV = config.get("component_shared","enable_pv")
        AOS.enableKibanaOps = config.get("logging","enable_kibana_ops")
        AOS.ESRam = config.get("logging","elastic_ram")
        AOS.RegistryQEToken = config.get("component_shared","registryqe_token")
        AOS.TokenUser = config.get("component_shared","token_user")
        AOS.deployMode = config.get("component_shared", "deploy_mode")
        AOS.TokenUserEMail = config.get("component_shared","token_user_email")
        AOS.ESClusterSize = config.get("logging","elastic_cluster_size")
        AOS.PVCSize = config.get("component_shared","pvc_size")
        AOS.EFKDeployer = config.get("logging","efk_deployer")
        AOS.cassandraNodes = config.get("metrics","cassandra_nodes")
        AOS.useJournal = config.get("logging", "use_journal")
        AOS.userWriteAccess = config.get("metrics","user_write_access")
        AOS.dynamicallyPV = config.get("metrics","dynamically_provision_storage")

        if AOS.osUser:
           AOS.osProject = re.match(r'\w+',AOS.osUser).group(0)
        
        arg_map_to_param = {'m': 'master',
                            'p': 'osProject',
                            'd': 'delProject',
                            'pull': 'pullLoggingMetricsImage',
                            'ose': 'isOSEServer',
                            'prefix': 'imagePrefix',
                            'mtag': 'imageVersion',
                            'mode': 'deployMode',
                           }
        existedArgs = vars(args).items()
        for arg,value in existedArgs:
            aosVar = arg_map_to_param.get(arg)
            if value and aosVar: 
               setattr(AOS, aosVar, value)

    # Get the OpenShift service public port
    @classmethod
    def set_master_server_port(cls):
        cprint("Getting service port from master server:", "blue")
        masterConfig = os.path.join(AOS.masterConfigRoot, AOS.masterConfigFile)
        outputs = AOS.run_ssh_command("sed -n '/^assetConfig:/,/^corsAllowedOrigins:/p' {}| grep bindAddress:| head -1".format(masterConfig))
        if outputs:
           AOS.masterPort = outputs.split(":")[-1].strip()
        
    @staticmethod
    def set_masterUrl():
       if AOS.lbHost:
          AOS.MasterURL = "https://{}:{}".format(AOS.lbHost, AOS.masterPort)
       else:
          AOS.MasterURL = "https://{}:{}".format(AOS.master, AOS.masterPort)

    @staticmethod
    def show_user_info():
        cprint("User info:",'blue')
        print("LB host: {}".format(AOS.lbHost))
        print("master: {}".format(AOS.master))
        print("port: {}".format(AOS.masterPort))
        print("user: {}".format(AOS.osUser))
        print("project: {}".format(AOS.osProject))
        print("image prefix: {}".format(AOS.imagePrefix))
        print("image version: {}".format(AOS.imageVersion))
     
    @staticmethod
    def get_current_time_str():
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def echo_command(cmd="Please wait..."):
        cprint("[{}]Running Command: {}\n".format(AOS.get_current_time_str(), cmd),'magenta')

    @staticmethod
    def echo(msg):
        prefix_str = '>' * len('Running Command')
        print("[{}]: {}".format(prefix_str, msg))

    # Check if can ssh into the master host
    @staticmethod
    def ssh_validation():
        try:
            command = "date > /dev/null"
            remote_command = '%s {}'.format(pipes.quote(command)) % AOS.SSHIntoMaster
            returncode = check_call(remote_command, shell=True,)
            return returncode
        except Exception, errMsg:
            os.sys.exit()

    @staticmethod
    def set_ssh_master():
        ssh = "ssh"
        scp = "scp"
        if "root" != AOS.masterUser:
           ssh = "ssh -t"
           scp = "scp -t"
        AOS.SSHIntoMaster = ssh +" -i %s -o identitiesonly=yes -o ConnectTimeout=10 %s@%s" % (os.path.expanduser(AOS.pemFile), AOS.masterUser, AOS.master)
        AOS.ScpFileFromMaster = scp + " -i %s -o identitiesonly=yes -o ConnectTimeout=10 %s@%s:" % (os.path.expanduser(AOS.pemFile), AOS.masterUser, AOS.master)

    # Check if the configrations are set correctly.
    @classmethod
    def check_validation(cls,args):
        cprint("Checking Confiurations...",'blue')
        if not os.path.isfile(AOS.osConfigFile):
            cprint("Please create your config file by:","red")
            cprint("easy-aos.py cfg","blue")
            sys.exit(1)

        AOS.get_config(args)

        notification_items = []
        if not AOS.master:
            notification_items.append("[global].master")
        if not AOS.osUser:
            notification_items.append("[global].os_user")
        if not AOS.pemFile:
            notification_items.append("[ssh].pem_file")
        if not AOS.osUserToken and not AOS.osPasswd:
            notification_items.append("[global].os_passwd OR [global].os_user_token")

        if 0 < len(notification_items):
            cprint("Please set below parameter(s) in %s:" % os.path.abspath(AOS.osConfigFile),'green',on_color='on_blue',attrs=['bold'])
            cprint('\n'.join(notification_items),'green')
            os.sys.exit()

        AOS.set_ssh_master()
        AOS.ssh_validation()
        cprint("Local configrations are OK. Good!",'green')
        if "root" != AOS.masterUser:
           AOS.set_oc_oadm_with_path()
        AOS.set_master_server_port()
        AOS.set_masterUrl()
        if not AOS.imageVersion:
           AOS.imageVersion = AOS.get_image_tag_version()
        AOS.show_user_info()

    @classmethod
    def set_oc_oadm_with_path(cls):
        oadm_output = AOS.run_ssh_command("whereis oadm")
        oc_output = AOS.run_ssh_command("whereis oc")
        AOS.oadmWithPathOnMaster = oadm_output.split()[1]
        AOS.ocWithPathOnMaster = oc_output.split()[1]

    @staticmethod
    def get_image_tag_version():
        cprint("Get the master major version to set image version tag","blue")
        output = AOS.run_ssh_command("oadm version")
        if output:
           tagVersion = re.match("oadm\s+v(\d+\.\d+\.\d+).*",output).group(1)
           return tagVersion
        return "latest"

    # Execute oc related commands on master host or local machine
    @staticmethod
    def run_ssh_command(cmd, asShell=True,ssh=True,expectedNum=None,echoRe=None):
        remote_command = cmd

        if ssh:
            remote_command = '%s {}'.format(pipes.quote(AOS.sudo_hack(cmd))) % AOS.SSHIntoMaster
            if "root" != AOS.masterUser and "oc " in remote_command:
               remote_command = remote_command.replace("oc ",AOS.ocWithPathOnMaster+" ")
            if "root" != AOS.masterUser and "oadm " in remote_command:
               remote_command = remote_command.replace("oadm ",AOS.oadmWithPathOnMaster+" ")

        echo_msg = remote_command
        if expectedNum:
           echo_msg += ", expected num: {}({})".format(expectedNum,echoRe)
        AOS.echo_command(echo_msg)

        try:
            outputs = check_output(remote_command, shell=asShell, stderr=STDOUT)
            if "ssh " in remote_command:
                list_o = outputs.split('\n')
                if "atomic-openshift" in outputs:
                    return list_o[:-2]
                else:
                    return outputs
            else:
                return outputs
        except (CalledProcessError,OSError), e:
            if e.output and not re.match(".*(which|cannot be updated|no process found|not found|request did not complete|refused|Service Unavailable|Unable to connect).*",  e.output):
                AOS.echo_command(remote_command)
                cprint(e.output,'red')
                cprint("Aborted!!!",'red',attrs=['bold'])
                os.sys.exit()
            elif "command" in e.output:
                scpFileCMD = AOS.ScpFileFromMaster+"/etc/origin/master/admin.kubeconfig ."
                check_output(scpFileCMD, shell=asShell, stderr=STDOUT)
                localCMD = '{} --config={}'.format(cmd, 'admin.kubeconfig')
                outputs = check_output(localCMD, shell=asShell, stderr=STDOUT)
                if "ssh " in remote_command:
                  list_o = outputs.split('\n')
                  if "atomic-openshift" in outputs:
                    return list_o[:-2]
                  else:
                    return outputs
                else:
                   return outputs

    # Add permission for serviceaccount or user
    @classmethod
    def do_permission(cls,role_type,role_name,user=None):

        if not user:
            user = AOS.osUser
        enableSSH = False
        pre_cmd = "oc policy"
        if re.match(r".*(cluster|scc-).*",role_type):
            enableSSH = True
            pre_cmd = "oadm policy"
        if "add-" in role_type:
            if "cluster" in role_type:
                cprint("Note: *%s* user has '%s' admin role! Be Careful!!!" % (user,role_name),'red')
            else:
                cprint("Added '%s' role to *%s* user!" % (role_name,user),'blue')
        elif "remove-" in role_type:
            cprint("Removed '%s' role from *%s* user." % (role_name,user),'green')
        command = "%s %s %s %s" % (pre_cmd,role_type,role_name,user)
        AOS.run_ssh_command(command,ssh=enableSSH)

    # Check the status for resource
    @staticmethod
    def resource_validate(cmd, reStr, dstNum=3, enableSsh=False):
        cprint("Wait above operation to finished...",'blue')

        iloop = 50
        interval = 6
        timeout = iloop * interval
        output = ""
        while dstNum > len(re.findall(reStr,output)) and 0 < iloop:
            time.sleep(interval)
            iloop -= 1
            output = AOS.run_ssh_command(cmd,ssh=enableSsh,expectedNum=dstNum,echoRe=reStr)

        if iloop == 0:
            cprint("Operation is not finished, timeout {} seconds".format(timeout),'yellow')
            os.sys.exit()

    @classmethod
    def add_project(cls):
        if AOS.delProject:
           if "deploy" not in AOS.deployMode:
              cprint("Deleting project *{}*".format(AOS.osProject),'blue')
              project = re.findall(AOS.osProject,AOS.run_ssh_command("oc get project",ssh=False))
              if 0 < len(project):
                 AOS.run_ssh_command("oc delete project {}".format(AOS.osProject),ssh=False)
                 AOS.resource_validate("oc get projects", r"{}\s+".format(AOS.osProject), dstNum=0)
           else:
              AOS.cleanup_metics()

        outputs = AOS.run_ssh_command("oc get projects", ssh=False)
        project = re.findall(r"{}\s+".format(AOS.osProject), outputs)
        if 0 == len(project):
            cprint("Creating project *{}*".format(AOS.osProject),'blue')
            AOS.run_ssh_command("oc new-project {}".format(AOS.osProject),ssh=False)

        AOS.run_ssh_command("oc project {}".format(AOS.osProject), ssh=False)

    # Make sure "oc login" on time by manual
    @staticmethod
    def loginedOnce():
        loginCMD = AOS.get_login_cmd(AOS.MasterURL)

        fExist = os.path.exists(os.path.expanduser('~/.kube/config'))
        master = AOS.lbHost if AOS.lbHost else AOS.master
        if not fExist or not AOS.run_ssh_command("grep {} ~/.kube/config".format(master), ssh=False):
            cprint("[ IMPORTANT ] Need login this master once by manual! [ IMPORTANT ]",'red')
            cprint("Please run below login command line:",'red')
            cprint(loginCMD,'green')
            os.sys.exit()

    @classmethod
    def get_login_cmd(cls,masterUrl):
        loginCMD = ""
        if AOS.osPasswd:
           loginCMD = "oc login %s -u %s -p %s" % (masterUrl,AOS.osUser,AOS.osPasswd)
        elif AOS.osUserToken:
           loginCMD = "oc login --token=%s --server=%s" % (AOS.osUserToken,masterUrl)
        return loginCMD

    @classmethod
    def login_server(cls):
        AOS.loginedOnce()
        cprint('Log into OpenShift...','blue')
        loginCMD = AOS.get_login_cmd(AOS.MasterURL)
        AOS.run_ssh_command(loginCMD,ssh=False)
        AOS.add_project()

    @classmethod
    def get_subdomain(cls):
        cprint("Getting dns subdomain from master server:", "blue")
        masterConfig = os.path.join(AOS.masterConfigRoot, AOS.masterConfigFile)
        outputs = AOS.run_ssh_command("grep subdomain {}".format(masterConfig))
        subdomain = outputs.split()[-1].strip('"')
        return subdomain

    # Delete oauthclients objects for logging deployment
    @classmethod
    def delete_oauth(cls):
        oauth = re.findall(r"kibana-proxy", AOS.run_ssh_command("oc get oauthclients", ssh=False))
        if 0 < len(oauth):
            AOS.run_ssh_command("oc delete oauthclients kibana-proxy", ssh=False)
            AOS.resource_validate("oc get oauthclients",r"kibana-proxy",dstNum=0)
            AOS.run_ssh_command("oc delete oauthclients kibana-proxy -n openshift", ssh=False)
            AOS.resource_validate("oc get oauthclients",r"kibana-proxy -n openshift",dstNum=0)


    # Patch insecure registry label for logging deployment(image tag <=3.2.1)
    @classmethod
    def set_annotation(cls, imageStreams):
        cprint('Import tags for imagestreams...','blue')
        isList = [x.split()[0] for x in imageStreams.strip().split('\n')]
        for osIS in isList:
            AOS.run_ssh_command('oc patch imagestreams {}  -p {}'.format(osIS, pipes.quote('{"metadata":{"annotations":{"openshift.io/image.insecureRepository":"true"}}}')), ssh=False)
            if "registry.qe" not in AOS.imagePrefix:
              AOS.run_ssh_command('oc import-image {imgstream}:{version} --from={imgpre}{imgstream}:{version} --insecure=true'.format(imgstream=osIS, version=AOS.imageVersion, imgpre=AOS.imagePrefix), ssh=False)
            else:
              AOS.run_ssh_command('oc tag --source=docker {}{}:{} {}:{}'.format(AOS.imagePrefix, osIS, AOS.imageVersion, osIS, AOS.imageVersion), ssh=False)
              AOS.run_ssh_command('oc import-image {imgpre}{imgstream}:{version} --insecure=true --confirm'.format(imgstream=osIS, version=AOS.imageVersion, imgpre=AOS.imagePrefix), ssh=False)
            time.sleep(5)

    @staticmethod
    def update_dc_for_registryqe_repo():
        dcs = AOS.run_ssh_command("oc get dc --no-headers -n {}".format(AOS.osProject), ssh=False)
        dcList = [x.split()[0] for x in dcs.strip().split('\n')]
        AOS.run_ssh_command("oc get dc logging-kibana -o yaml > dc.json", ssh=False)
        AOS.run_ssh_command("sed -i -e 's#image: logging-kibana#image: registry.qe.openshift.com/openshift3/logging-kibana:3.2.0#g' -e 's#image: openshift-auth-proxy#image: registry.qe.openshift.com/openshift3/logging-auth-proxy:3.2.0#g' dc.json", ssh=False)
        AOS.run_ssh_command("oc replace -f dc.json", ssh=False)
        AOS.run_ssh_command("oc get dc logging-fluentd -o yaml > dc.json", ssh=False)
        AOS.run_ssh_command("sed -i 's#image: logging-fluentd#image: registry.qe.openshift.com/openshift3/logging-fluentd:3.2.0#g' dc.json", ssh=False)
        AOS.run_ssh_command("oc replace -f dc.json", ssh=False)
        for dc in dcList:
            if "es" in dc:
               AOS.run_ssh_command("oc get dc {} -o yaml > dc.json".format(dc), ssh=False)
               AOS.run_ssh_command("sed -i 's#image: logging-elasticsearch#image: registry.qe.openshift.com/openshift3/logging-elasticsearch:3.2.0#g' dc.json", ssh=False)
               AOS.run_ssh_command("oc replace -f dc.json", ssh=False)

        AOS.run_ssh_command("rm -f dc.json", ssh=False)

    @staticmethod
    def create_secret_for_registryqe():
        cprint("Creating docker pull secret for registry.qe","blue")
        hasSecret = AOS.run_ssh_command("oc get secret -n {} | grep mysecret".format(AOS.osProject), ssh=False)
        if not hasSecret:
           AOS.run_ssh_command("oc secrets new-dockercfg mysecret --docker-server=registry.qe.openshift.com --docker-username={} --docker-email={} --docker-password={}".format(AOS.TokenUser, AOS.TokenUserEMail, AOS.RegistryQEToken), ssh=False)

    @staticmethod
    def add_pull_secret_for_registryqe_repo(saList=["aggregated-logging-elasticsearch","aggregated-logging-fluentd","aggregated-logging-kibana"]):
        if not AOS.RegistryQEToken or not AOS.TokenUser or not AOS.TokenUserEMail:
           cprint("Please set 'registryqe_token', 'token_user' and 'token_user_email' under [image] section!", "red")
           sys.exit(1)
        AOS.create_secret_for_registryqe()
        cprint("Adding docker pull secret for registry.qe","blue")
        for sa in saList:
            AOS.run_ssh_command("oc secrets add {} mysecret --for=pull".format(sa), ssh=False)

    # Add public url for logging/metrics in master config file
    @classmethod
    def add_weburl_for_logging_and_metrics(cls):
        masterConfig = os.path.join(AOS.masterConfigRoot, AOS.masterConfigFile)
        subdomain = AOS.get_subdomain()
        #add_weburl_cmd = "sed -i -e '/loggingPublicURL:/d' -e '/metricsPublicURL:/d' -e '/publicURL:/a\  loggingPublicURL: https://{kibana_ops_appname}.{sub_domain}' -e '/publicURL:/a\  loggingPublicURL: https://{kibana_appname}.{sub_domain}' -e '/publicURL:/a\  metricsPublicURL: https://{hawkular_metrics_appname}.{sub_domain}/hawkular/metrics' {master_config}".format(kibana_ops_appname=AOS.kibanaOpsAppname, sub_domain=subdomain, kibana_appname=AOS.kibanaAppname, hawkular_metrics_appname=AOS.hawkularMetricsAppname, master_config=masterConfig)
        add_weburl_cmd = "sed -i -e '/loggingPublicURL:/d' -e '/metricsPublicURL:/d' -e '/publicURL:/a\  loggingPublicURL: https://{kibana_appname}.{sub_domain}' -e '/publicURL:/a\  metricsPublicURL: https://{hawkular_metrics_appname}.{sub_domain}/hawkular/metrics' {master_config}".format(kibana_ops_appname=AOS.kibanaOpsAppname, sub_domain=subdomain, kibana_appname=AOS.kibanaAppname, hawkular_metrics_appname=AOS.hawkularMetricsAppname, master_config=masterConfig)
        AOS.run_ssh_command(add_weburl_cmd)

    @classmethod
    def restart_ose_server(cls):
        master_server_name = AOS.run_ssh_command("systemctl list-unit-files|grep atomic-openshift-master | awk '{print $1}'")
        for sname in master_server_name:
            sname = sname.replace("\x0d","")
            AOS.run_ssh_command("systemctl restart {}".format(sname))

    # Enable logging/metrics on OpenShift console
    @classmethod
    def enable_logging_metircs_web_console(cls):
        AOS.add_weburl_for_logging_and_metrics()
        if "amazonaws" in AOS.master and not AOS.isOSEServer:
           AOS.restart_origin_server()
        else:
           AOS.restart_ose_server()

    @staticmethod
    def make_para_list(paraMap):
        para_list = []
        for p_name, p_value in paraMap.items():
            para_list.append(p_name+"="+p_value)
        return para_list

    @staticmethod
    def cleanup_metics():
        cprint("Cleanuping metrics deployments under project *{}*".format(AOS.osProject),'blue')
        deleted_obj_with_lable = ["all","secrets","sa","templates","pvc"]
        deleted_obj_without_lable = ["sa metrics-deployer","secret metrics-deployer","secret mysecret"]
        for obj in deleted_obj_with_lable:
            AOS.run_ssh_command("oc delete {} --selector=metrics-infra -n {}".format(obj,AOS.osProject), ssh=False)
        for obj in deleted_obj_without_lable:
            AOS.run_ssh_command("oc delete {} -n {}".format(obj,AOS.osProject), ssh=False)
    
    @staticmethod
    def update_metric_deployer_template(project="openshift"):
        if AOS.imageVersion >= "3.3.0":
           hasWriteAccessParameter = AOS.run_ssh_command("oc get template metrics-deployer-template  -o yaml -n {}| grep USER_WRITE_ACCESS".format(project))
           if not hasWriteAccessParameter:
              cprint("Updating metrics deployer template in project {}".format(project), "blue")
              AOS.run_ssh_command("oc get template metrics-deployer-template  -o yaml -n {proj} > ~/metrics-deployer-template.bak.old && oc delete template metrics-deployer-template -n {proj}; oc create -f {tpFile} -n {proj}".format(proj=project,tpFile=AOS.HCHStack))

    # Deploy metrics stack
    @classmethod
    def start_metrics_stack(cls):
        if "openshift" in AOS.osProject:
           AOS.do_permission("add-cluster-role-to-user", "cluster-admin")
        AOS.login_server()
        AOS.update_metric_deployer_template()

        cprint("{} metrics stack...".format(AOS.deployMode),'blue')
        if "deploy" == AOS.deployMode:
           AOS.run_ssh_command("oc create serviceaccount metrics-deployer",ssh=False)
           AOS.do_permission("add-cluster-role-to-user", "cluster-reader", user="system:serviceaccount:%s:heapster" % AOS.osProject)
           AOS.do_permission("add-role-to-user","edit", user="system:serviceaccount:%s:metrics-deployer" % AOS.osProject)
           AOS.run_ssh_command("oc secrets new metrics-deployer nothing=/dev/null",ssh=False)
           if "registry.qe" in AOS.imagePrefix:
              AOS.add_pull_secret_for_registryqe_repo(["metrics-deployer"])
        subdomain = AOS.get_subdomain()
        paraList = AOS.make_para_list({'HAWKULAR_METRICS_HOSTNAME':AOS.hawkularMetricsAppname+'.'+subdomain,\
                                     'IMAGE_PREFIX':AOS.imagePrefix,\
                                     'IMAGE_VERSION':AOS.imageVersion,\
                                     'USE_PERSISTENT_STORAGE':AOS.enablePV,\
                                     'MASTER_URL':AOS.MasterURL,\
                                     'CASSANDRA_NODES': AOS.cassandraNodes,\
                                     'CASSANDRA_PV_SIZE':AOS.PVCSize})
        if AOS.imageVersion >= "3.2.0" and AOS.imageVersion < "3.3.0":
           paraList.extend(AOS.make_para_list({'MODE':AOS.deployMode}))
        elif AOS.imageVersion >= "3.3.0":
           paraList.extend(AOS.make_para_list({'MODE':AOS.deployMode,'USER_WRITE_ACCESS':AOS.userWriteAccess,'DYNAMICALLY_PROVISION_STORAGE':AOS.dynamicallyPV}))

        AOS.run_ssh_command("oc new-app metrics-deployer-template -p {}".format(','.join(paraList)), ssh=False)
        if "registry.qe" in AOS.imagePrefix:
           output = AOS.run_ssh_command("oc get pod --no-headers -n {}|grep metrics-deployer".format(AOS.osProject), ssh=False)
           deployerPodName = output.split()[0]
           AOS.resource_validate("oc get pods --no-headers -n {}".format( AOS.osProject),r".*metrics-deployer.*Running.*",dstNum=1)
           AOS.resource_validate("oc logs {} -n {}".format(deployerPodName, AOS.osProject),r".*VALIDATING THE DEPLOYMENT.*",dstNum=1)
           AOS.add_pull_secret_for_registryqe_repo(["heapster","hawkular","cassandra"])
        AOS.resource_validate("oc get pods -n %s" % AOS.osProject,r".*[heapster|hawkular].*1/1.*Running.*")
        if "openshift" in AOS.osProject:
           AOS.do_permission("remove-cluster-role-from-user", "cluster-admin")
        cprint("Success!","green")

    @classmethod
    def clean_logging_objects(cls):
        cprint("Cleanup resources related to logging stack...",'blue')
        AOS.run_ssh_command("oc delete all --selector logging-infra=kibana", ssh=False)
        AOS.run_ssh_command("oc delete all --selector logging-infra=fluentd", ssh=False)
        AOS.run_ssh_command("oc delete all --selector logging-infra=elasticsearch", ssh=False)
        AOS.run_ssh_command("oc delete all,sa --selector logging-infra=support", ssh=False)
        AOS.run_ssh_command("oc delete sa logging-deployer", ssh=False)
        AOS.run_ssh_command("oc delete oauthclients kibana-proxy", ssh=False)
        AOS.run_ssh_command("oc delete secret logging-deployer logging-fluentd logging-elasticsearch logging-es-proxy logging-kibana logging-kibana-proxy logging-kibana-ops-proxy", ssh=False)
        AOS.run_ssh_command("oc delete ClusterRole daemonset-admin -n openshift && oc delete ClusterRole oauth-editor -n openshift")
        AOS.run_ssh_command("oc delete ClusterRole rolebinding-reader -n openshift")

    @staticmethod
    def set_mode_for_logging():
        if "deploy" == AOS.deployMode:
           AOS.deployMode = "install"
        if "redeploy" == AOS.deployMode:
           AOS.deployMode = "reinstall"

    @staticmethod
    def update_logging_deployer_template(project="openshift"):
        cprint("Updating logging deployer template in project {}".format(project), "blue")
        output = AOS.run_ssh_command("oc get template logging-deployer-template -o yaml -n {proj} | grep image: ".format(proj=project))
        if AOS.imageVersion >= "3.3.0" and "logging-deployer" not in output:
           AOS.run_ssh_command("oc get template logging-deployer-template -o yaml -n {proj} | sed  's/\(image:\s.*\)logging-deployment\(.*\)/\\1logging-deployer\\2/g' | oc apply -n {proj} -f -".format(proj=project))
        elif AOS.imageVersion < "3.3.0" and "logging-deployment" not in output:
           AOS.run_ssh_command("oc get template logging-deployer-template -o yaml -n {proj} | sed  's/\(image:\s.*\)logging-deployer\(.*\)/\\1logging-deployment\\2/g' | oc apply -n {proj} -f -".format(proj=project))

    # Deploy / re-deploy logging metrics
    @classmethod
    def start_logging_stack(cls):
        AOS.set_mode_for_logging()
        AOS.do_permission("add-cluster-role-to-user", "cluster-admin")
        #AOS.update_logging_deployer_template()
        if "reinstall" in AOS.deployMode:
           AOS.redeploy_logging()
        elif "install" in AOS.deployMode:
           AOS.deploy_logging()

        AOS.resource_validate("oc get pods -n {}".format(AOS.osProject), r"logging-deployer.+Completed", dstNum=1)
        if AOS.imageVersion <= "3.2.1":
           AOS.run_ssh_command("oc process logging-support-template -n {project} -v IMAGE_VERSION={version}| oc create -n {project} -f -".format(project=AOS.osProject,version=AOS.imageVersion), ssh=False)
           imageStreams = AOS.run_ssh_command("oc get is --no-headers -n {}".format(AOS.osProject), ssh=False)
           AOS.set_annotation(imageStreams)
        dcNum = 3
        if "true" in AOS.enableKibanaOps:
           dcNum += 2
           if AOS.imageVersion > "3.2.1":
              dcNum += 1
        AOS.resource_validate("oc get dc --no-headers -n {}".format(AOS.osProject), r"(logging-fluentd\s+|logging-kibana\s+|logging-es-\w+|logging-curator\s+|logging-curator-ops\s+|logging-kibana-ops\s+)", dstNum=dcNum)

        if AOS.imageVersion <= "3.2.1":
           nodeNum = AOS.run_ssh_command("oc get node --no-headers 2>/dev/null | grep -v Disabled |grep -i -v Not | wc -l", ssh=True).strip()
           AOS.run_ssh_command("oc scale dc/logging-fluentd --replicas={}".format(nodeNum), ssh=False)
           AOS.run_ssh_command("oc scale rc/logging-fluentd-1 --replicas={}".format(nodeNum), ssh=False)
        else:
           AOS.run_ssh_command("oc scale dc/logging-curator --replicas=1", ssh=False)
           AOS.run_ssh_command("oc scale rc/logging-curator-1 --replicas=1", ssh=False)
           AOS.run_ssh_command("oc scale dc/logging-curator-ops --replicas=1", ssh=False)
           AOS.run_ssh_command("oc scale rc/logging-curator-ops-1 --replicas=1", ssh=False)

        AOS.resource_validate("oc get pods -n {}".format(AOS.osProject), r"logging-\w+.+[1/1|2/2].+Running", dstNum=dcNum)
        AOS.do_permission("remove-cluster-role-from-user", "cluster-admin")
        cprint("Success!","green")
   
    @classmethod
    def redeploy_logging(cls):
        AOS.run_ssh_command('oc project {}'.format(AOS.osProject),ssh=False)
        AOS.run_ssh_command('oc patch configmap logging-deployer  -p {}'.format(pipes.quote('{"data":{"use-journal":"'+AOS.useJournal+'"}}')), ssh=False)
        AOS.run_ssh_command('oc patch configmap logging-deployer  -p {}'.format(pipes.quote('{"data":{"enable-ops-cluster":"'+AOS.enableKibanaOps+'"}}')), ssh=False)
        AOS.run_ssh_command('oc patch configmap logging-deployer  -p {}'.format(pipes.quote('{"data":{"es-cluster-size":"'+AOS.ESClusterSize+'"}}')), ssh=False)
        cmd = "oc new-app logging-deployer-template -p IMAGE_PREFIX={},IMAGE_VERSION={},MODE={}".format(AOS.imagePrefix,AOS.imageVersion,AOS.deployMode)
        AOS.run_ssh_command(cmd,ssh=False)
 
    @classmethod
    def deploy_logging(cls):
        AOS.login_server()
        cprint("Start deploying logging stack pods...",'blue')
        AOS.clean_logging_objects()
        subdomain = AOS.get_subdomain()
        AOS.run_ssh_command("oc secrets new logging-deployer nothing=/dev/null",ssh=False)

        paraList = AOS.make_para_list({'ENABLE_OPS_CLUSTER':AOS.enableKibanaOps,\
                                     'IMAGE_PREFIX':AOS.imagePrefix,\
                                     'IMAGE_VERSION':AOS.imageVersion,\
                                     'KIBANA_HOSTNAME':AOS.kibanaAppname+'.'+subdomain,\
                                     'MASTER_URL':AOS.MasterURL,\
                                     'PUBLIC_MASTER_URL':AOS.MasterURL,\
                                     'ES_INSTANCE_RAM':AOS.ESRam,\
                                     'ES_CLUSTER_SIZE':AOS.ESClusterSize,\
                                     'KIBANA_OPS_HOSTNAME':AOS.kibanaOpsAppname+'.'+subdomain})
        if AOS.imageVersion >= "3.3.0":
           AOS.run_ssh_command("oc new-app logging-deployer-account-template", ssh=False)
           AOS.do_permission("add-cluster-role-to-user","oauth-editor",user="system:serviceaccount:{}:logging-deployer".format(AOS.osProject))
           AOS.do_permission("add-cluster-role-to-user","cluster-reader",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))
           AOS.do_permission("add-scc-to-user","privileged",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))
           #To deploy without PV:
           AOS.run_ssh_command("oc create configmap logging-deployer  --from-literal kibana-hostname={}.{} --from-literal public-master-url={} --from-literal es-cluster-size={} --from-literal enable-ops-cluster={} --from-literal use-journal={} --from-literal kibana-ops-hostname={}.{} --from-literal es-instance-ram={} --from-literal es-nodeselector=logging-infra-fluentd=true --from-literal kibana-nodeselector=logging-infra-fluentd=true --from-literal curator-nodeselector=logging-infra-fluentd=true".format(AOS.kibanaAppname,subdomain,AOS.MasterURL,AOS.ESClusterSize,AOS.enableKibanaOps,AOS.useJournal,AOS.kibanaOpsAppname,subdomain,AOS.ESRam), ssh=False)
           #To enable dynamicPV (dynamic PV):
           #AOS.run_ssh_command("oc create configmap logging-deployer  --from-literal kibana-hostname={}.{} --from-literal public-master-url={} --from-literal es-cluster-size={} --from-literal enable-ops-cluster={} --from-literal use-journal={} --from-literal kibana-ops-hostname={}.{} --from-literal es-instance-ram={} --from-literal es-pvc-dynamic=true --from-literal es-pvc-size=1G --from-literal es-ops-pvc-size=1G".format(AOS.kibanaAppname,subdomain,AOS.MasterURL,AOS.ESClusterSize,AOS.enableKibanaOps,AOS.useJournal,AOS.kibanaOpsAppname,subdomain,AOS.ESRam), ssh=False)

           #To enable PV (non-dynamic PV):
           #AOS.run_ssh_command("oc create configmap logging-deployer  --from-literal kibana-hostname={}.{} --from-literal public-master-url={} --from-literal es-cluster-size={} --from-literal enable-ops-cluster={} --from-literal use-journal={} --from-literal kibana-ops-hostname={}.{} --from-literal es-instance-ram={} --from-literal es-pvc-size=1G --from-literal es-ops-pvc-size=1G".format(AOS.kibanaAppname,subdomain,AOS.MasterURL,AOS.ESClusterSize,AOS.enableKibanaOps,AOS.useJournal,AOS.kibanaOpsAppname,subdomain,AOS.ESRam), ssh=False)
           AOS.run_ssh_command("oc label node -l registry=enabled logging-infra-fluentd=true --overwrite", ssh=False)
           if AOS.imageVersion >= "3.4.0":
              AOS.do_permission("add-cluster-role-to-user","rolebinding-reader",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))
        elif AOS.imageVersion > "3.2.1" and AOS.imageVersion < "3.3.0":
           AOS.do_permission("add-scc-to-user","hostmount-anyuid",user="system:serviceaccount:{}:aggregated-logging-elasticsearch".format(AOS.osProject))
           AOS.run_ssh_command("oc new-app logging-deployer-account-template", ssh=False)
           AOS.do_permission("add-role-to-user","edit",user="--serviceaccount logging-deployer")
           AOS.do_permission("add-role-to-user","daemonset-admin",user="--serviceaccount logging-deployer")
           AOS.do_permission("add-cluster-role-to-user","oauth-editor",user="system:serviceaccount:{}:logging-deployer".format(AOS.osProject))
           AOS.do_permission("add-cluster-role-to-user","cluster-reader",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))
           AOS.do_permission("add-scc-to-user","privileged",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))
           AOS.run_ssh_command("oc label node -l registry=enabled logging-infra-fluentd=true --overwrite", ssh=False)
           if "true" in AOS.enablePV:
              paraList.extend(AOS.make_para_list({'ES_PVC_SIZE':AOS.PVCSize,'ES_PVC_PREFIX':'es-pv-','MODE':AOS.deployMode}))
        else:
           AOS.delete_oauth()
           AOS.do_permission("add-scc-to-user","hostmount-anyuid",user="system:serviceaccount:{}:aggregated-logging-elasticsearch".format(AOS.osProject))
           AOS.run_ssh_command('echo -e "apiVersion: v1\nkind: ServiceAccount\nmetadata:\n    name: logging-deployer\nsecrets:\n- name: logging-deployer"| oc create -f -', ssh=False)
           AOS.do_permission("add-role-to-user","edit",user="system:serviceaccount:{}:logging-deployer".format(AOS.osProject))
           AOS.do_permission("add-cluster-role-to-user","cluster-reader",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))
           AOS.do_permission("add-scc-to-user","privileged",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))
           if AOS.imageVersion == "3.2.1":
              paraList.extend(AOS.make_para_list({'MODE':AOS.deployMode}))
           #AOS.do_permission("add-cluster-role-to-user","cluster-admin",user="system:serviceaccount:{}:logging-deployer".format(AOS.osProject))
           #AOS.do_permission("add-scc-to-user","hostmount-anyuid",user="system:serviceaccount:{}:aggregated-logging-fluentd".format(AOS.osProject))

        if AOS.imageVersion <= "3.2.1":
           if "registry.qe" in AOS.imagePrefix:
              AOS.add_pull_secret_for_registryqe_repo()

        if AOS.imageVersion < "3.3.0":
           cmd = "oc new-app logging-deployer-template -p {}".format(','.join(paraList))
        else:
           cmd = "oc new-app logging-deployer-template -p IMAGE_PREFIX={},IMAGE_VERSION={},MODE={}".format(AOS.imagePrefix,AOS.imageVersion,AOS.deployMode)
        AOS.run_ssh_command(cmd,ssh=False)

    # Git clone metrics/logging/apiman for OpenShift origin env if needed
    @staticmethod
    def clone_gitrepo(repoName):
        cprint("Clone git repo for {}".format(repoName),"blue")
        dirContent = AOS.run_ssh_command("test -d {};echo $?".format(repoName))
        if "0" == dirContent.strip():
           AOS.run_ssh_command("pushd {} && git pull && popd".format(repoName))
           if "logging" in repoName:
           #    AOS.run_ssh_command("pushd {}/deployer/common && git pull && popd".format(repoName))
               AOS.run_ssh_command("pushd {}/kibana-proxy && git pull && popd".format(repoName))
        else:
           AOS.run_ssh_command("git clone https://github.com/openshift/{}.git".format(repoName))
           if "logging" in repoName:
           #    AOS.run_ssh_command("git clone https://github.com/openshift/origin-integration-common.git {}/deployer/common".format(repoName))
               AOS.run_ssh_command("git clone https://github.com/fabric8io/openshift-auth-proxy.git {}/kibana-proxy".format(repoName))

    @staticmethod
    def clean_apiman():
        AOS.run_ssh_command("oc delete -f https://raw.githubusercontent.com/openshift/origin-apiman/master/deployer/deployer.yaml -n openshift")
    
    @staticmethod
    def get_inner_registry_svcIPPort():
        # format 172.30.20.237:5000
        registryIpPort = AOS.run_ssh_command('oc get svc docker-registry --template="{{.spec.portalIP}}:{{ with index .spec.ports 0 }}{{ .port }}{{end}}"')
        return registryIpPort+"/apiman/"

    # Deploy apiman stack [Deprecated]
    @classmethod
    def start_apiman_stack(cls):
        #AOS.clone_gitrepo("origin-apiman")
        AOS.clean_apiman()
        AOS.login_server()
        cprint("starting APIMan stack...",'blue')
        imagePrefix = AOS.get_inner_registry_svcIPPort()
        AOS.run_ssh_command("oc new-app -f origin-apiman/hack/dev-builds.yaml", ssh=False)
        AOS.run_ssh_command("oc create -n openshift -f https://raw.githubusercontent.com/openshift/origin-apiman/master/deployer/deployer.yaml")
        AOS.run_ssh_command("oc secrets new apiman-deployer nothing=/dev/null", ssh=False)
        AOS.run_ssh_command("oc new-app apiman-deployer-account-template", ssh=False)
        AOS.do_permission("add-role-to-user", "edit", user="--serviceaccount apiman-deployer")
        AOS.do_permission("add-cluster-role-to-user", "cluster-reader", user="system:serviceaccount:%s:apiman-console" % AOS.osProject)
        AOS.do_permission("add-cluster-role-to-user", "cluster-reader", user="system:serviceaccount:%s:apiman-gateway" % AOS.osProject)
        subdomain = AOS.get_subdomain()
        paraList = AOS.make_para_list({'GATEWAY_HOSTNAME':'gateway.'+subdomain,\
                                     'CONSOLE_HOSTNAME':'console.'+subdomain,\
                                     'IMAGE_PREFIX':AOS.imagePrefix,\
                                     'IMAGE_VERSION':AOS.imageVersion,\
                                     'PUBLIC_MASTER_URL':AOS.MasterURL,\
                                     'ES_CLUSTER_SIZE':AOS.ESClusterSize})
        AOS.run_ssh_command("oc new-app apiman-deployer-template -p {}".format(','.join(paraList)), ssh=False)
        AOS.resource_validate("oc get pods -n %s" % AOS.osProject,r"[apiman\-console|apiman\-curator|apiman\-es|apiman\-gateway].*Running.*", 4)
        cprint("Success!","green")
        cprint("Access APIMan Console via browser: ~/link.html", "green")

    # Use "sudo" when starting OpenSfhit origin service
    @staticmethod
    def sudo_hack(cmd):
       if "root" != AOS.masterUser:
          return "sudo " + cmd
      # elif "openshift" in cmd:
      #    return 
       return cmd

    @staticmethod
    def restart_origin_server():
        openshift = "/data/src/github.com/openshift/origin/_output/local/bin/linux/amd64/openshift"
        outputs = AOS.run_ssh_command("hostname")
        nodeConfigPath = '/etc/origin/node-' + outputs.strip()
        nodeConfig = os.path.join(nodeConfigPath,"node-config.yaml")
        masterConfig = os.path.join(AOS.masterConfigRoot, AOS.masterConfigFile)
        kubeConfig = os.path.join(AOS.masterConfigRoot, AOS.kubeConfigFile)
        master = AOS.master.replace('.','-')

        killRs = AOS.run_ssh_command("%s openshift; echo $?" % "killall")
        #killRs = AOS.run_ssh_command("%s openshift; echo $?" % AOS.sudo_hack("killall"))
        if not "0" in killRs:
           AOS.run_ssh_command("%s start --public-master=%s:8443 --write-config=/etc/origin" % (openshift, AOS.master))
           AOS.run_ssh_command("echo export KUBECONFIG={kube} >> ~/.bashrc; {chd} o+rx {kube}".format(chd="chmod",kube=kubeConfig))

        AOS.run_ssh_command("nohup {os} start --node-config={node} --master-config={master} &> openshift.log &".format(os=openshift,node=nodeConfig,master=masterConfig))
        if not "0" in killRs:
           AOS.resource_validate("oc get projects", r"Active", enableSsh=True)
           # For automation cases related admin role
           AOS.run_ssh_command("oc config use-context default/%s:8443/system:admin && %s -p /root/.kube && %s /etc/origin/master/admin.kubeconfig /root/.kube/config"\
                            % (master,'mkdir','cp'))

    # Start OpenShift origin service
    @classmethod
    def start_origin_openshift(cls):
        cprint("Starting OpenShift Service...","blue")
        AOS.restart_origin_server()
        outputs = AOS.run_ssh_command("oc get pods -n default")
        allRunningPods = re.findall(r'docker-registry.*Running.*|router-1.*Running.*', outputs)
        if 0 == len(allRunningPods):
            AOS.create_default_pods()
            AOS.create_imagestream_under("openshift")
            AOS.create_template_under("openshift","origin-apiman")
            AOS.create_template_under("openshift","origin-metrics")
            AOS.create_template_under("openshift","origin-aggregated-logging")
            #AOS.clone_gitrepo("origin-apiman")
            #AOS.clone_gitrepo("origin-metrics")
            #AOS.clone_gitrepo("origin-aggregated-logging")
            if AOS.pullLoggingMetricsImage:
               AOS.pull_metrics_and_logging_images()
        cprint("Success! OpenShift Server is UP. ^_^",'green')

    @staticmethod
    def create_template_under(project, repoName):
        cprint("Creating templates for {} in *openshift* namespace...".format(repoName),'blue')
        yamlFile = "deployer/deployer.yaml"
        if "metrics" in repoName:
           yamlFile = "metrics.yaml"
        cmd = "oc create -n {prj} -f https://raw.githubusercontent.com/openshift/{repo}/master/{yf}".format(prj=project, repo=repoName, yf=yamlFile)
        AOS.run_ssh_command(cmd)

    @staticmethod
    def create_imagestream_under(project):
        cprint("Creating basic imagestream in *openshift* namespace...",'blue')
        cmd = "oc create -n {} -f https://raw.githubusercontent.com/openshift/origin/master/examples/image-streams/image-streams-rhel7.json".format(project)
        AOS.run_ssh_command(cmd)

    @staticmethod
    def pull_metrics_and_logging_images():
        cprint("Pulling down metrics and logging images form DockerHub registry...",'blue')
        imagePrefixs = ["openshift/origin-","registry.access.redhat.com/openshift3/"]
        images = ["metrics-hawkular-metrics","metrics-heapster","metrics-cassandra","metrics-deployer",\
                  "logging-kibana","logging-fluentd","logging-elasticsearch","logging-auth-proxy","logging-deployment"]
        cmd = ';'.join([' '.join(['docker pull',imagePrefix+image]) for imagePrefix in imagePrefixs for image in images])
        AOS.run_ssh_command(cmd)


    @staticmethod
    def delete_resource(resource):
        enabledSSH = False
        resource, rtype, project = resource.split(":")
        delRsc = resource
        if not resource:
           delRsc = "--all"
        delCmd = "oc delete {rtp} {rsc} -n {prj}".format(rtp=rtype, rsc=delRsc, prj=project)
        getCmd = "oc get {rtp} {rsc} -n {prj}".format(rtp=rtype, rsc=resource, prj=project)
        if re.match("(default|openshift)", project):
            enabledSSH = True

        resources = AOS.run_ssh_command(getCmd, ssh=enabledSSH)
        if resources:
           AOS.run_ssh_command(delCmd, ssh=enabledSSH)

    # Create router and docker registry pods for OpenShift origin
    @staticmethod
    def create_default_pods():
        resourceList = [":templates:openshift",":dc:default",":rc:default",":pod:default","docker-registry:svc:default","router:svc:default",":imagestreams:openshift","router:sa:default","router-router-role:clusterrolebinding:default","registry:sa:default","registry-registry-role:clusterrolebinding:default"]
        for resource in resourceList:
            AOS.delete_resource(resource)
        # Add permission for creating router
        AOS.run_ssh_command("oadm policy add-scc-to-user privileged system:serviceaccount:default:default")
        #chmod = AOS.sudo_hack('chmod')
        cprint("Creating registry and router pods",'blue')
        preCmd = 'export CURL_CA_BUNDLE=/etc/origin/master/ca.crt; \
                  {chd} a+rwX /etc/origin/master/admin.kubeconfig; \
                  {chd} +r /etc/origin/master/openshift-registry.kubeconfig;'.format(chd="chmod")
        AOS.run_ssh_command(preCmd)
       #          oc create serviceaccount registry -n default; \
       #           oc create serviceaccount router -n default; \
        createCmd = "oadm policy add-scc-to-user hostnetwork -z router;\
                     oadm policy add-cluster-role-to-user system:router system:serviceaccount:default:router; \
                     oadm  router --service-account=router;\
                     oadm registry -n default --config=/etc/origin/master/admin.kubeconfig;"
        AOS.run_ssh_command(createCmd)

    # The enter point for sub-commands
    @classmethod
    def args_handler(cls):
        # Global options
        commonArgs = ArgumentParser(add_help=False)
        commonArgs.add_argument("-m", help="OpenShift server DNS,eg: ec2-52-23-180-133.compute-1.amazonaws.com")
        commonArgs.add_argument("--version", action="version", version="%(prog)s 1.0", help="Display version")
    
        # Options for sub-command
        subCommonArgs = ArgumentParser(add_help=False)
        subCommonArgs.add_argument('-p', help="Specify OpenShift project")
        subCommonArgs.add_argument('-d', action="store_true",\
                                         help="Delete OpenShift project and Re-create. Default is False")
        subCommonArgs.add_argument('--prefix',help="Image prefix, eg:brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888/openshift3/")
        subCommonArgs.add_argument('--mtag',help="Image tag, eg: latest")
        subCommonArgs.add_argument('--mode',help="Deploy mode, like: deploy|install|...")
    
        commands = ArgumentParser(parents=[commonArgs],description="Setup OpenShift on EC2 or Deploy metrics/logging stack")
        subCommands = commands.add_subparsers(title='subcommands:')
    
        # Sub-command for starting OpenShift server
        startos = subCommands.add_parser('startos', parents=[commonArgs],\
                                                    description="Start OpenShift origin server",\
                                                    help="start OpenShift origin service")
        startos.add_argument('--pull', action="store_true",\
                                       help="Docker pull the metrics and logging related images from DockerHub.Default is False")
        startos.set_defaults(subcommand=AOS.start_origin_openshift)
    
        # Sub-command for deploying metrics stack
        metrics = subCommands.add_parser('metrics',parents=[commonArgs,subCommonArgs],\
                                                   description="Deploy metrics stack pods",\
                                                   help="Deploy metrics stack pods")
        metrics.set_defaults(subcommand=AOS.start_metrics_stack)
    
        # Sub-command for deploying logging stack
        logging = subCommands.add_parser('logging', parents=[commonArgs,subCommonArgs],\
                                                    description="Deploy logging stack pods",\
                                                    help="Deploy logging stack pods")
        logging.set_defaults(subcommand=AOS.start_logging_stack)
    
        # Sub-command for deploying APIMan stack
        apiman = subCommands.add_parser('apiman', parents=[commonArgs,subCommonArgs],\
                                                    description="Deploy APIMan stack pods [Deprecated]",\
                                                    help="Deploy APIMan stack pods [Deprecated]")
        apiman.set_defaults(subcommand=AOS.start_apiman_stack)

        # Enable logging and metrics view in OpenShift console
        webconsole = subCommands.add_parser('webconsole', parents=[commonArgs],\
                                                    description="Enable logging and metrics view in OpenShift console",\
                                                    help="Enable logging and metrics view in OpenShift console")
        webconsole.add_argument('--ose', action="store_true",\
                                       help="Indicate the OpenShift is OSE env.Default is False")
        webconsole.set_defaults(subcommand=AOS.enable_logging_metircs_web_console)

        # Show current configurations
        showcfg = subCommands.add_parser('showcfg', parents=[commonArgs],\
                                                    description="Show current configurations",\
                                                    help="Show current configurations")
        showcfg.set_defaults(subcommand=AOS.show_current_config)

        # Generate default config file
        cfg = subCommands.add_parser('cfg', description="Generate default config file",\
                                                    help="Generate default config file")
        cfg.set_defaults(subcommand=AOS.generate_default_config)

        args = commands.parse_args()
        if not re.match("(show_current_config|generate_default_config)", args.subcommand.__name__):
           AOS.check_validation(args)
     
        return args

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    args = AOS.args_handler() 
    args.subcommand()
