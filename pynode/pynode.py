import os
import sys
import argparse
import logging
import json

from configparser import ConfigParser
from manager import Manager
from broker import Broker
from patterns.exceptions import ContractsAbiNotFound
from webapi.web_socket_listener import WebSocket
from tools.worker_tools import WorkerMaker


# -------------------------------------
# main pynode launcher
# -------------------------------------
def run_pynode():
    try:
        manager = Manager.get_instance()
        # startup broker main process
        broker = Broker(eth_server=manager.eth_host,
                        abi_path=manager.eth_abi_path,
                        pandora=manager.eth_pandora,
                        node=manager.eth_worker,
                        data_dir=manager.ipfs_storage,
                        ipfs_server=manager.ipfs_host,
                        ipfs_port=manager.ipfs_port)
    except Exception as ex:
        logging.error("Error broker initialization: %s, exiting", type(ex))
        logging.error(ex.args)
        return

    if broker.connect() is False:
        return

    # Remove the following line in order to put the app into a daemon mode (running on the background)
    broker.join()


# -------------------------------------
# worker contract creator
# -------------------------------------
def run_worker_creation():
    try:
        manager = Manager.get_instance()
        worker = WorkerMaker(eth_server=manager.eth_host,
                             abi_path=manager.eth_abi_path,
                             pandora=manager.eth_pandora)
    except Exception as ex:
        logging.error("Error worker contract creation: %s, exiting", type(ex))
        logging.error(ex.args)
        return

    if worker.connect() is False:
        return
    else:
        customer_address = input("Please insert your address : ")
        worker.create_worker(customer_address)


# -------------------------------------
# primary pynode enter point
# -------------------------------------
def main(argv):
    help_message = """
        Pandora Boxchain python node realisation    
        
                -/////////+++++/`                
             `/ss:--:sds/d/````.hNso-             
           /hNhsoosh+.   `h+     ss`/ss`          
          so     yoh/      yy//+++dh- /h`         
         y+    `h/  yo  -ohM+...`.d+/sssm-        
       `hh++++od/    sds/-h:    `h:    -sN/       
      `dN`````-Mh`  .d- -mo::::/m:     `h/yo      
     .d:m     `m:d.-d/os++yds:-.:os+. .d-  oy`    
    -d.`m     `m .dmy/`     -ossooshNdN-    +d    
    so :Mhoooood: so          :Mh`    :d.  -NM    
    so/h`y+     y++o          :d:d.    .d-:d.N    
    sNs   os     oNo          -d .dsoooosNd``N`   
    :d     dhmdsooyyo:      -odm: s+     os +y    
     :h` `y/ `/oo/..-+hh+:os+ho`y+o+     osos     
      .h:h:     `d+/////N/ `y+   oNo     +Mo      
       `dh:    .h-    `h:-oyh    `dsoo++oN+       
        `yyos+:d-````-mds/` /h` `h:    `h/        
          oo .oN+++++od`     -h:d-    `h:         
           /s/`/h`    :h.    -shyoosmmh-          
             .+shd.    .d:/ss/` `/ss/`            
                `/ooo+++oooo+++++-                
                                                     
        to see more https://pandoraboxchain.ai/ 
        
        Current configuration performs launch with different parameters and configurations
         
        example >python ./pynode.py - starts pynode with default config 
                                      placed in pynode.ini file 
                                      and use SOFT launch mode 
                                             'ganache' eth_connector instance 
                                             'local' config for ipfs 

        if we need launch with different ETH HOST and IPFS config use launch params
        example >python ./pynode.py -e (--etherum) remote -i (--ipfs) infura
                    - starts pynoode in SOFT mode
                    with eth_connector instance to connect remote  = http://bitcoin.pandora.network:4444
                    and IPFS infura config server = https://ipfs.infura.io
                                           port = 5001

        -m (--mode) is integer value that performs launch mode definition
            0 = 'SOFT' - production launch in daemon mode
            1 = 'HARD' - develop mode with raise exceptions and stopping process

        -c (--config) performs path for custom config file for launch params
        -a (--abi) performs change abi directory path

        -w (--worker) alow to set custom worker contract address
                      seted by console value will replace value in config file
                      for this launch

        -o (--obtain) provides an opportunity to create Worker node contract,
                      Balance as well as authority will be assigned to this contract
                      To prevent loss of progress please store the address in a safe place
                      
    """

    parser = argparse.ArgumentParser(description=help_message, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-m',
                        '--mode',
                        action="store",
                        dest='launch_mode',
                        default='0',
                        help='launch mode for pynode, '
                             'set value "1" for launch in strict, '
                             'develop mode (default value is 0)',
                        metavar='')
    parser.add_argument('-c',
                        '--config',
                        action="store",
                        dest='configuration_file',
                        default='../pynode.ini',
                        help='startup pyrrha-pynode with custom configuration file '
                             '(default is ../pynode.ini)',
                        metavar='')
    parser.add_argument('-e',
                        '--ethereum',
                        action="store",
                        dest='ethereum_use',
                        default='ganache',
                        help='setting up current used host for ethereum node '
                             '(default is local)',
                        metavar='')
    parser.add_argument('-a',
                        '--abi',
                        action='store',
                        dest='abi_path',
                        default='../abi',
                        help='setting up path to folder with ABI files '
                             '(default is ../abi)',
                        metavar='')
    parser.add_argument('-i',
                        '--ipfs',
                        action='store',
                        dest='ipfs_use',
                        default='local',
                        help='setting up current used host for ipfs connection '
                             '(default is local)',
                        metavar='')
    parser.add_argument('-w',
                        '--worker',
                        action='store',
                        dest='worker_node',
                        help='setting up currently created worker contract address ',
                        metavar='')
    parser.add_argument('-o',
                        '--obtain',
                        action='store_true',
                        dest='create_worker',
                        default=False,
                        help='Provides an opportunity to create Worker node contract')
    parser.add_argument('-v ',
                        '--version',
                        action='version',
                        version='%(prog)s 0.9.1')

    results = parser.parse_args()

    # read configuration file and parse base settings
    print("Configuration file path      : " + str(results.configuration_file))
    if results.configuration_file:
        try:
            config = ConfigParser()
            config.read(results.configuration_file)
            eth_section = config['Ethereum']
            eth_contracts = config['Contracts']
            ipfs_section = config['IPFS']
            web_section = config['Web']
            eth_host = eth_section[results.ethereum_use]
            pandora_address = eth_contracts['pandora']
            worker_address = eth_contracts['worker_node']
            eth_hooks = eth_contracts['hooks']
            pynode_start_on_launch = eth_contracts['start_on_launch']
            ipfs_storage = ipfs_section['store_in']
            ipfs_use_section = config['IPFS.%s' % results.ipfs_use]
            ipfs_host = ipfs_use_section['server']
            ipfs_port = ipfs_use_section['port']
            socket_enable = web_section['enable']
            socket_host = web_section['host']
            socket_port = web_section['port']
            socket_listen = web_section['connections']
        except Exception as ex:
            print("Error reading config: %s, exiting", type(ex))
            logging.error(ex.args)
            return
    print("Config reading success")
    manager = Manager.get_instance()

    # -------------------------------------
    # create worker node contract
    # -------------------------------------
    if results.create_worker:
        manager.pynode_config_file_path = results.configuration_file
        manager.eth_host = eth_host
        manager.eth_abi_path = results.abi_path
        manager.eth_pandora = pandora_address

        print('Pynode start to obtain new Worker node contract')
        print("Ethereum use                 : " + str(results.ethereum_use))
        print("Ethereum host                : " + str(eth_host))
        print("Primary contracts addresses")
        print("Pandora main contract        : " + str(pandora_address))
        # inst contracts
        instantiate_contracts(results, eth_hooks)
        print("ABI initialize success")
        # launch worker node creation
        run_worker_creation()
        return

    # -------------------------------------
    # launch pynode
    # -------------------------------------
    if results.worker_node:
        worker_contract_address = results.worker_node
    else:
        worker_contract_address = worker_address

    manager.pynode_config_file_path = results.configuration_file
    manager.launch_mode = results.launch_mode
    manager.eth_use = results.ethereum_use
    manager.eth_host = eth_host
    manager.eth_abi_path = results.abi_path
    manager.eth_pandora = pandora_address
    manager.eth_worker = worker_contract_address
    manager.ipfs_use = results.ipfs_use
    manager.ipfs_host = ipfs_host
    manager.ipfs_port = ipfs_port
    manager.ipfs_storage = ipfs_storage
    manager.pynode_start_on_launch = pynode_start_on_launch
    manager.web_socket_enable = socket_enable
    manager.web_socket_host = socket_host
    manager.web_socket_port = socket_port
    manager.web_socket_listeners = socket_listen

    print("Pynode production launch")
    print("Node launch mode             : " + str(results.launch_mode))
    print("Ethereum use                 : " + str(results.ethereum_use))
    print("Ethereum host                : " + str(eth_host))
    print("Primary contracts addresses")
    print("Pandora main contract        : " + str(pandora_address))
    print("Worker node contract         : " + str(worker_contract_address))
    print("IPFS configuration")
    print("IPFS use                     : " + str(results.ipfs_use))
    print("IPFS host                    : " + str(ipfs_host))
    print("IPFS port                    : " + str(ipfs_port))
    print("IPFS file storage            : " + str(ipfs_storage))
    print("Web socket enable            : " + str(socket_enable))
    # inst contracts
    instantiate_contracts(results, eth_hooks)
    # launch socket web listener
    if socket_enable == 'True':
        print("Launch client socket listener")
        print("Web socket enable            : " + str(manager.web_socket_enable))
        print("Web socket host              : " + str(manager.web_socket_host))
        print("Web socket port              : " + str(manager.web_socket_port))
        print("Web socket listeners         : " + str(manager.web_socket_listeners))
        WebSocket(socket_host, socket_port, socket_listen)
    # launch pynode
    if pynode_start_on_launch == 'True':
        print("Launch node")
        run_pynode()


# -------------------------------------
# read and store contracts abi
# -------------------------------------
def instantiate_contracts(results, eth_hooks):
    manager = Manager.get_instance()
    print("ABI folder path              : " + str(results.abi_path))
    if os.path.isdir(results.abi_path):
        if eth_hooks:
            if os.path.isfile(results.abi_path + "\PandoraHooks.json"):
                with open(results.abi_path + "\PandoraHooks.json", encoding='utf-8') as pandora_contract_file:
                    manager.eth_pandora_contract = json.load(pandora_contract_file)['abi']
        else:
            if os.path.isfile(results.abi_path + "\Pandora.json"):
                with open(results.abi_path + "\Pandora.json", encoding='utf-8') as pandora_contract_file:
                    manager.eth_pandora_contract = json.load(pandora_contract_file)['abi']

        if os.path.isfile(results.abi_path + "\WorkerNode.json"):
            with open(results.abi_path + "\WorkerNode.json", encoding='utf-8') as worker_contract_file:
                manager.eth_worker_contract = json.load(worker_contract_file)['abi']
        if os.path.isfile(results.abi_path + "\CognitiveJob.json"):
            with open(results.abi_path + "\CognitiveJob.json", encoding='utf-8') as eth_cognitive_job_contract:
                manager.eth_cognitive_job_contract = json.load(eth_cognitive_job_contract)['abi']
        if os.path.isfile(results.abi_path + "\Kernel.json"):
            with open(results.abi_path + "\Kernel.json", encoding='utf-8') as eth_kernel_contract:
                manager.eth_kernel_contract = json.load(eth_kernel_contract)['abi']
        if os.path.isfile(results.abi_path + "\CognitiveJob.json"):
            with open(results.abi_path + "\Dataset.json", encoding='utf-8') as eth_dataset_contract:
                manager.eth_dataset_contract = json.load(eth_dataset_contract)['abi']
        print("ABI loading success")
    else:
        print("ABI files not found, exiting")
        raise ContractsAbiNotFound()


# -------------------------------------
# main launcher
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv)


# -------------------------------------
# docker configurator
# -------------------------------------
def use_env_cfg():
    config_tmp = open('../pynode.tmp.ini', "r")
    config_file = open('../pynode.ini', "w")
    while 1:
        line = config_tmp.readline()
        if not line:
            break
        if os.environ['ETHEREUM_HOST']:
            line = line.replace('ETHEREUM_HOST', os.environ['ETHEREUM_HOST'])
        if os.environ['ETHEREUM_LOCAL_HOST']:
            line = line.replace('ETHEREUM_LOCAL_HOST', os.environ['ETHEREUM_LOCAL_HOST'])
        if os.environ['IPFS_INFURA_HOST']:
            line = line.replace('IPFS_INFURA_HOST', os.environ['IPFS_INFURA_HOST'])
        if os.environ['IPFS_PANDORA_HOST']:
            line = line.replace('IPFS_PANDORA_HOST', os.environ['IPFS_PANDORA_HOST'])
        if os.environ['IPFS_LOCALHOST']:
            line = line.replace('IPFS_LOCALHOST', os.environ['IPFS_LOCALHOST'])
        if os.environ['CONTRACT_PANDORA']:
            line = line.replace('CONTRACT_PANDORA', os.environ['CONTRACT_PANDORA'])
        if os.environ['CONTRACT_WORKER_NODE']:
            line = line.replace('CONTRACT_WORKER_NODE', os.environ['CONTRACT_WORKER_NODE'])
        config_file.write(line)
    config_file.close()
    config_tmp.close()
    print('=======================================')
    print(open('../pynode.ini').read())
    print('=======================================')

