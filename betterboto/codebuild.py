import types
import logging
import time


logger = logging.getLogger(__file__)


def start_build_and_wait_for_completion(self, **kwargs):
    """
    This will start a build of an AWS CodeBuild Project and wait for it to complete.
    It will return the result of the build.

    :param self: codebuild client
    :param kwargs: these are passed onto the start_build method call
    :return: codebuild_client.batch_get_builds.response[0]
    """
    build = self.start_build(
        **kwargs
    ).get('build')
    build_id = build.get('id')

    while build.get('buildStatus') == 'IN_PROGRESS':
        response = self.batch_get_builds(ids=[build_id])
        build = response.get('builds')[0]
        time.sleep(5)
        logger.info("Current status: {}".format(build.get('buildStatus')))

    return build


def make_better(client):
    client.start_build_and_wait_for_completion = types.MethodType(start_build_and_wait_for_completion, client)
    return client
