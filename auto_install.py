import subprocess
import fileinput
import os
import socket


print "--------Basic configuration------"
cmds = ["setenforce 0", "yum -y install yum-utils -y", "yum-config-manager --add https://copr.fedorainfracloud.org/coprs/tendrl/release/repo/epel-7/tendrl-release-epel-7.repo", "yum-config-manager --add https://copr.fedorainfracloud.org/coprs/tendrl/dependencies/repo/epel-7/tendrl-dependencies-epel-7.repo", "yum -y install epel-release -y", "service firewalld stop", "systemctl disable firewalld", "iptables --flush"]

for cmd in cmds:
    os.system(cmd)


ip = raw_input("Enter the ip addr of etcd node = ")

print "---------Installing node-agent and node-monitoring----------"
cmds = ["yum -y install tendrl-node-agent -y", "yum -y install tendrl-node-monitoring -y", ""]
for cmd in cmds:
    os.system(cmd)

print "--------Configuring node agent ----------"
textToSearch = "0.0.0.0"
textToReplace = ip
tempFile = open( "/etc/tendrl/node-agent/node-agent.conf.yaml", 'r+' )
for line in fileinput.input( "/etc/tendrl/node-agent/node-agent.conf.yaml" ):
    if textToSearch in line :
        line  = ( line.replace( textToSearch,  textToReplace) )
    tempFile.write(line)
tempFile.close()

print "----Configuring node monitoring------"
tempFile = open( "/etc/tendrl/node-monitoring/node-monitoring.conf.yaml", 'r+' )
for line in fileinput.input( "/etc/tendrl/node-monitoring/node-monitoring.conf.yaml" ):
    if "0.0.0.0" in line:
        line = ( line.replace( "0.0.0.0",  ip) )
    tempFile.write(line)
tempFile.close()

machine = raw_input("***Please enter server/node:")
if machine == "server":
    print "------Install etcd-------"
    os.system("yum -y install etcd -y")
    print "------Configuring etcd-------"
    tempFile = open( "/etc/etcd/etcd.conf", 'r+' )
    textToSearch = "http://localhost:2379"
    textToReplace = "http://%s:2379" % ip
    for line in fileinput.input( "/etc/etcd/etcd.conf" ):
        if textToSearch in line :
            line  = ( line.replace( textToSearch,  textToReplace) )
        tempFile.write(line)
    tempFile.close()

    print "------Start etcd------"
    cmds = ["systemctl enable etcd", "systemctl start etcd"]
    for cmd in cmds:
        os.system(cmd)
    print "------Start node-agent and node monitoring-------"
    cmds = ["systemctl enable tendrl-node-agent", "systemctl start tendrl-node-agent", "systemctl enable tendrl-node-monitoring", "systemctl start tendrl-node-monitoring"] 
    for cmd in cmds:
        os.system(cmd)

    print "-------Install tendrl-api----------"
    os.system("yum -y install tendrl-api -y")
    print "--------Configure tendrl-api--------"
    tempFile = open( "/etc/tendrl/etcd.yml", 'r+' )
    f = False
    for line in fileinput.input( "/etc/tendrl/etcd.yml" ):
        if "production" in line:
            f = True
        if "127.0.0.1" in line and f:
            line = ( line.replace( "127.0.0.1",  ip) )
        if "user_name" in line and f:
            line = "  :user_name: ''    \n"
        if ":password" in line and f:
            line = "  :password: ''      \n"
        tempFile.write(line)
    tempFile.close()
    print "-------start tendrl-api-------"
    cmds = ["systemctl start tendrl-api", "systemctl restart httpd"]
    for cmd in cmds:
        os.system(cmd)
    
    print "-------Install performance monitoring----------"
    os.system("yum -y install tendrl-performance-monitoring -y")
    print "--------Configure performance monitoring--------"
    cmds = ["/usr/lib/python2.7/site-packages/graphite/manage.py syncdb --noinput", "chown apache:apache /var/lib/graphite-web/graphite.db", "systemctl enable carbon-cache", "systemctl start carbon-cache", "systemctl restart httpd"]
    for cmd in cmds:
        os.system(cmd)
    tempFile = open( "/etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml", 'r+' )
    for line in fileinput.input( "/etc/tendrl/performance-monitoring/performance-monitoring.conf.yaml" ):
        if "0.0.0.0" in line:
            line = ( line.replace( "0.0.0.0",  ip) )
        tempFile.write(line)
    tempFile.close()
    print "------start performance monitoring------"
    cmds = ["systemctl enable tendrl-performance-monitoring", "systemctl start tendrl-performance-monitoring"]
    for cmd in cmds:
        os.system(cmd)
    
    print "-----Install dash board------"
    os.system("yum -y install tendrl-dashboard -y")
    os.system("systemctl restart httpd")

    print "------Create user------"
        
    p = subprocess.Popen(["RACK_ENV=production rake etcd:load_admin"], cwd="/usr/share/tendrl-api/", shell=True)
    p.wait()

else:
    type = raw_input("***Please enter node type ceph/gluster:")
    provisioner = raw_input("***Provisioner yes/no:")
    if type == "ceph":
        if provisioner == "no":
            role = raw_input("***Node is mon/osd:")
            if role == "mon":
                print "----configuring ceph mon------"
                os.system("yum-config-manager --add http://download-node-02.eng.bos.redhat.com/rcm-guest/ceph-drops/auto/ceph-1.3-rhel-7-compose/latest-RHCEPH-1.3-RHEL-7/compose/MON/x86_64/os/")
                file = "/etc/yum.repos.d/download-node-02.eng.bos.redhat.com_rcm-guest_ceph-drops_auto_ceph-2-rhel-7-compose_latest-RHCEPH-2-RHEL-7_compose_MON_x86_64_.repo"
                tempFile = open(file, "r+")
                for line in fileinput.input(file):
                    if "added from: " in line:
                        line = ( line.replace( "added from: ",  '') )
                    tempFile.write(line)
                tempFile.write("gpgcheck = 0 \n")
                tempFile.close()
            else:
                print "----configuring ceph osd------"
                os.system("yum-config-manager --add  http://download-node-02.eng.bos.redhat.com/rcm-guest/ceph-drops/auto/ceph-1.3-rhel-7-compose/latest-RHCEPH-1.3-RHEL-7/compose/OSD/x86_64/os/")
                file = "/etc/yum.repos.d/download-node-02.eng.bos.redhat.com_rcm-guest_ceph-drops_auto_ceph-2-rhel-7-compose_latest-RHCEPH-2-RHEL-7_compose_OSD_x86_64_.repo"
                tempFile = open(file, "r+")
                for line in fileinput.input(file):
                    if "added from: " in line:
                        line = ( line.replace( "added from: ",  '') )
                    tempFile.write(line)
                tempFile.write("gpgcheck = 0 \n")
                tempFile.close()
        else:
            print "----configuring ceph provisioner------"
            file = "/etc/tendrl/node-agent/node-agent.conf.yaml"
            tempFile = open(file, "a+")
            tempFile.write("  - provisioner/ceph")
            tempFile.close()
         
            os.system("yum-config-manager --add http://download-node-02.eng.bos.redhat.com/rcm-guest/ceph-drops/auto/rhscon-2-rhel-7-compose/latest-RHSCON-2-RHEL-7/compose/Installer/x86_64/os/")
            file = "/etc/yum.repos.d/download-node-02.eng.bos.redhat.com_rcm-guest_ceph-drops_auto_rhscon-2-rhel-7-compose_latest-RHSCON-2-RHEL-7_compose_Installer_x86_64_os_.repo"
            tempFile = open(file, "r+")
            for line in fileinput.input(file):
                if "added from: " in line:
                    line = ( line.replace( "added from: ",  '') )
                tempFile.write(line)
            tempFile.write("gpgcheck = 0 \n")
            tempFile.close()
            print "----Installing ceph installer------"
            os.system("yum -y install ceph-installer -y")
    else:
        if provisioner == "yes":
            print "----configuring gluster provisioner------"
            file = "/etc/tendrl/node-agent/node-agent.conf.yaml"
            tempFile = open(file, "a+")
            tempFile.write("  - provisioner/gluster")
            tempFile.close()             
            os.system("yum-config-manager --add  https://copr.fedorainfracloud.org/coprs/sac/gdeploy/repo/epel-7/sac-gdeploy-epel-7.repo")
    cmds = ["systemctl enable tendrl-node-agent", "systemctl start tendrl-node-agent", "systemctl enable tendrl-node-monitoring", "systemctl start tendrl-node-monitoring"]
    for cmd in cmds:
        os.system(cmd)

print "----sucessfully configured----"
