from functools import partial
from typing import Generator, List

import boto3

iot = boto3.client('iot')


def unpaginate(method, element_name):
    nextToken = None
    while True:
        if nextToken is None:
            result = method()
        else:
            result = method(nextToken=nextToken)
        nextToken = result.get("nextToken")
        for item in result[element_name]:
            yield item
        if nextToken is None:
            break


class ThingGroup(object):
    def __init__(self, arn: str, name: str, things: List = None):
        if things is None:
            things = []
        self.arn = arn
        self.name = name
        self.things = things

    def __eq__(lhs, rhs):  # pylint: disable=no-self-argument
        return lhs.arn == rhs.arn

    def __ne__(lhs, rhs):  # pylint: disable=no-self-argument
        return lhs.arn != rhs.arn

    def __repr__(self):
        return "ThingGroup<%r>" % self.arn

    @staticmethod
    def try_from_loose(group: dict, things=None):
        if isinstance(group, ThingGroup):
            return group
        if isinstance(group, str):
            group = ThingGroup("", group)
            return group.sync()
        if group.get("groupArn") is not None:
            return ThingGroup(group["groupArn"], group["groupName"], things)
        else:
            return ThingGroup(group["thingGroupArn"], group["thingGroupName"],
                              things)

    def sync(self, create: bool = False, remote: bool = False):
        group = None
        # Try to get remote group
        for remote_group in get_groups():
            if remote_group.arn == self.arn:
                group = remote_group
        if group is None:
            try:
                group = ThingGroup.try_from_loose(iot.describe_thing_group(
                    thingGroupName=self.name))
            except:  # noqa
                if group is None and create:
                    group = ThingGroup.try_from_loose(iot.create_thing_group(
                        thingGroupName=self.name))
        if group is None:
            raise ValueError(self)

        # Sync data
        if remote:
            # ::TODO:: set remote name to local name
            raise NotImplementedError()
        else:
            self.arn = group.arn
            self.name = group.name

        if remote:
            group.things = list(get_things_for_group(group))

            # Sync remote things with local things
            if group.things != self.things:
                # Sync remote group with local group storage
                for thing in self.things:
                    if thing not in group.things:
                        iot.add_thing_to_thing_group(
                            thingGroupArn=group.arn,
                            thingArn=thing.arn
                        )
                # Sync remote with what doesn't exist in local
                for thing in group.things:
                    if thing not in self.things:
                        iot.remove_thing_from_thing_group(
                            thingGroupArn=group.arn,
                            thingArn=thing.arn
                        )
        else:
            self.things = list(get_things_for_group(group))

        return self


class Thing(object):
    def __init__(self, arn: str, name: str, groups: List[ThingGroup]=None):
        if groups is None:
            groups = []
        self.arn = arn
        self.name = name
        self.groups = groups

    def __eq__(lhs, rhs):  # pylint: disable=no-self-argument
        return lhs.arn == rhs.arn

    def __ne__(lhs, rhs):  # pylint: disable=no-self-argument
        return lhs.arn != rhs.arn

    def __repr__(self):
        return "Thing<%r>" % self.arn

    def get(self, key):
        if key == "thingName":
            return self.name
        elif key == "thingArn":
            return self.arn
        raise KeyError(key)

    @staticmethod
    def try_from_loose(thing, groups=None):
        if isinstance(thing, Thing):
            return thing
        if isinstance(thing, str):
            thing = Thing("", thing)
            thing.sync()
            return thing
        return Thing(thing["thingArn"], thing["thingName"], groups)

    def sync(self, create: bool = False, remote: bool = False):
        thing = None
        # Try to get Thing from ARN
        for remote_thing in get_things():
            if remote_thing.arn == self.arn:
                thing = remote_thing
        if thing is None:
            try:
                # Try to get the Thing by name
                thing = Thing.try_from_loose(iot.describe_thing(
                    thingName=self.name))
            except:  # noqa
                # Last case, make a new one
                if thing is None and create:
                    remote_thing = iot.create_thing(thingName=self.name)
                    thing = Thing.try_from_loose(remote_thing)

        if thing is None:
            raise ValueError(self)

        # Sync data
        if remote:
            # ::TODO:: set remote name to local name
            raise NotImplementedError()
        else:
            self.arn = thing.arn
            self.name = thing.name

        thing.groups = list(get_groups_for_thing(thing))

        # Sync remote groups with current groups
        if thing.groups != self.groups:
            # Add the remote thing to all groups the local thing is in
            for group in self.groups:
                if group not in thing.groups:
                    iot.add_thing_to_thing_group(
                        thingGroupArn=group.arn,
                        thingArn=thing.arn)
            # Remove the remote thing from all groups the local thing inn't
            for group in thing.groups:
                if group not in self.groups:
                    iot.remove_thing_from_thing_group(
                        thingGroupArn=group.arn,
                        thingArn=thing.arn
                    )
        return self

    def gen_credentials(self):
        # get current principals for thing
        principals = iot.list_thing_principals(thingName=self.name)
        short_name = self.arn.split("/")[-1]
        for cert in principals["principals"]:
            cert_id = cert.split("/")[-1]
            iot.update_certificate(certificateId=cert_id, newStatus="INACTIVE")
            iot.detach_thing_principal(thingName=short_name, principal=cert)
            iot.delete_certificate(certificateId=cert_id, forceDelete=True)
        values = iot.create_keys_and_certificate(setAsActive=True)
        cert = {
            "id": values["certificateId"],
            "arn": values["certificateArn"],
            "pem": values["certificatePem"]
        }
        keypair = (values["keyPair"]["PublicKey"],
                   values["keyPair"]["PrivateKey"])
        # attach policy to cert
        iot.attach_policy(
            policyName="devices-policy",
            target=cert["arn"])
        # attach cert to device
        # a cert is a "principal", so attach the Thing to the principal
        iot.attach_thing_principal(thingName=short_name, principal=cert["arn"])
        return cert, keypair, iot.describe_endpoint()


def get_things_for_group(group: dict) -> Generator[Thing, None, None]:
    group = ThingGroup.try_from_loose(group)
    part = partial(iot.list_things_in_thing_group,
                   thingGroupName=group.name)
    for thing in unpaginate(part, "things"):
        yield Thing.try_from_loose(thing)


def get_groups_for_thing(thing: dict) -> Generator[ThingGroup, None, None]:
    thing = Thing.try_from_loose(thing)
    part = partial(iot.list_thing_groups_for_thing,
                   thingName=thing.name)
    for group in unpaginate(part, "thingGroups"):
        yield ThingGroup.try_from_loose(group)


def get_things() -> Generator[Thing, None, None]:
    for thing in unpaginate(iot.list_things, "things"):
        groups = list(get_groups_for_thing(thing))
        yield Thing.try_from_loose(thing, groups=groups)


def get_groups() -> Generator[ThingGroup, None, None]:
    for group in unpaginate(iot.list_thing_groups, "thingGroups"):
        things = list(get_things_for_group(group))
        yield ThingGroup.try_from_loose(group, things=things)
