#!/usr/bin/python3

import boto3

def main():
    client = boto3.client('rds')
    ec2_client = boto3.client('ec2')
    dbs = client.describe_db_instances()
    for db in dbs['DBInstances']:
        open_ports = {}
        sg_ids = [sg['VpcSecurityGroupId'] for sg in db['VpcSecurityGroups']]
        for sg_id in sg_ids:
            sg = ec2_client.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]
            for permission in sg['IpPermissions']:
                if permission['FromPort'] == permission['ToPort']:
                    ports = permission['FromPort']
                else:
                    ports = "{}-{}".format(permission['FromPort'],permission['ToPort'])
                for IpRange in permission['IpRanges']:
                    key = IpRange['CidrIp']
                    desc = sg['GroupName']
                    if 'Description' in IpRange:
                        desc = "{}|{}".format(desc, IpRange['Description'])

                    if ports in open_ports:
                        if key in open_ports[ports]:
                            open_ports[ports][key][sg_id] = desc
                        else:
                            open_ports[ports][key] = {sg_id: desc}
                    else:
                        open_ports[ports] = {key: {sg_id: desc}}
                for UserIdGroupPair in permission['UserIdGroupPairs']:
                    source_sg_id = UserIdGroupPair['GroupId']
                    key = "{} ({})".format(source_sg_id, ec2_client.describe_security_groups(GroupIds=[source_sg_id])['SecurityGroups'][0]['GroupName'])

                    desc = sg['GroupName']
                    if 'Description' in UserIdGroupPair:
                        desc = "{}|{}".format(desc, UserIdGroupPair['Description'])

                    if ports in open_ports:
                        if key in open_ports[ports]:
                            open_ports[ports][key][sg_id] = desc
                        else:
                            open_ports[ports][key] = {sg_id: desc}
                    else:
                        open_ports[ports] = {key: {sg_id: desc}}
        for ports,sources in open_ports.items():
            for source in sorted(sources.keys()):
                sgs = []
                for sg_id in sorted(sources[source].keys()):
                    output = sg_id
                    if sources[source][sg_id]:
                        output = "{} ({})".format(output, sources[source][sg_id])
                    sgs.append(output)
                print("{: <40} {: <11} {: <70} {}".format(db['DBInstanceIdentifier'], ports, source, ", ".join(sgs)))

if __name__ == '__main__':
    main()
