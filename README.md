# My Treadmill Example

This example is inspired by a blog post [Using GitHub Actions for Greengrass v2 Continuous Deployment](https://devopstar.com/2022/09/22/github-actions-for-aws-iot-greengrass-v2-continuous-deployment) after a talk at [IoT Builders Session](https://twitter.com/i/spaces/1ynJOanQdpEKR). In here I use the same principal of deploying Greengrass component with GitHub Actions and OIDC.


## Greengrass Setup

Since I've been running this on a Raspberry Pi Zero W before installing Greengrass I had to install `openjdk-8-jre` as newer versions of java will not run on ARMv6 instruction set:

```
sudo apt update
sudo apt install openjdk-8-jre
```

After this run the following on the device (make sure you have AWS Credentials setup in on the device before running, like instructed [here](https://docs.aws.amazon.com/greengrass/v2/developerguide/getting-started.html)).

```bash
curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip && unzip greengrass-nucleus-latest.zip -d GreengrassCore

export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
export AWS_REGION="eu-west-1"
export GREENGRASS_THING_GROUP="home"
export GREENGRASS_THING_NAME="home-treadmill"

# For more: https://docs.aws.amazon.com/greengrass/v2/developerguide/getting-started.html#install-greengrass-v2
sudo -E java \
  -Droot="/greengrass/v2" \
  -Dlog.store=FILE -jar ./GreengrassCore/lib/Greengrass.jar \
  --aws-region ${AWS_REGION} \
  --thing-name ${GREENGRASS_THING_NAME} \
  --thing-group-name ${GREENGRASS_THING_GROUP} \
  --thing-policy-name GreengrassV2IoTThingPolicy \
  --tes-role-name GreengrassV2TokenExchangeRole \
  --tes-role-alias-name GreengrassCoreTokenExchangeRoleAlias \
  --component-default-user ggc_user:ggc_group \
  --provision true \
  --setup-system-service true \
  --deploy-dev-tools true
```

This will setup the Greengrass on the device with appropriate Thing Group and Thing Name in this scenario `home` and `home-treadmill` respectively.
As for the CD part of using the Github Actions, I’ve followed the instruction provided in the [blog post](https://devopstar.com/2022/09/22/github-actions-for-aws-iot-greengrass-v2-continuous-deployment).


# Timestream

To recreate the Timestream Database and Table deploy the bellow stack:

```
aws cloudformation deploy --template-file cfn/amazon-timestream/timestream.yaml --stack-name home-treadmill-timestream --capabilities CAPABILITY_IAM
```

# Grafana

First part to setting up Grafana is to create a role that has readonly access to Timestream
```
aws cloudformation deploy --template-file cfn/grafana/grafana-role.yaml --stack-name grafana-role --capabilities CAPABILITY_IAM

aws cloudformation describe-stacks --stack-name grafana-role --query "Stacks[0].Outputs[0].OutputValue"
```
This will give out an `arn` that will be used to create a Grafana workspace

```
aws grafana create-workspace --account-access-type CURRENT_ACCOUNT --authentication-providers AWS_SSO --permission-type SERVICE_MANAGED --workspace-data-sources TIMESTREAM --workspace-role-arn <ARN from grafana-role stack>
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
