# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Build the CIFuzz image on Google Cloud Builder.

Usage: build_cifuzz_images.py
"""

import os
import sys
import yaml

# pylint: disable=import-error
from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build

CIFUZZ_IMAGE = 'base-cifuzz'
PROJECT_ID = 'oss-fuzz-base'
TAG_PREFIX = 'gcr.io/{0}/'.format(PROJECT_ID)


def get_steps():
  """Gets the required steps to build the ci-fuzz image on gcr.

  Returns:
    A list of steps to be executed on google cloud.
  """
  steps = [{
      'args': [
          'clone',
          'https://github.com/google/oss-fuzz.git',
      ],
      'name': 'gcr.io/cloud-builders/git',
  }]

  steps.append({
      'args': [
          'build',
          '-t',
          TAG_PREFIX + CIFUZZ_IMAGE,
          '.',
      ],
      'dir': 'oss-fuzz/infra/cifuzz/' + CIFUZZ_IMAGE,
      'name': 'gcr.io/cloud-builders/docker',
  })

  return steps


def get_logs_url(build_id):
  """Gets the logs from the google cloud run instance.

  Args:
    build_id: The build id associated with the current build.

  Returns:
    A URL linking to the build logs.
  """
  url_format = ('https://console.developers.google.com/logs/viewer?'
                'resource=build%2Fbuild_id%2F{0}&project={1}')
  return url_format.format(build_id, PROJECT_ID)


def main():
  """Upload the CIFuzz docker image to Google container registry."""
  options = {}
  if 'GCB_OPTIONS' in os.environ:
    options = yaml.safe_load(os.environ['GCB_OPTIONS'])

  build_body = {
      'steps': get_steps(),
      'timeout': str(4 * 3600) + 's',
      'options': options,
      'images': [TAG_PREFIX + CIFUZZ_IMAGE],
  }

  credentials = GoogleCredentials.get_application_default()
  cloudbuild = build('cloudbuild', 'v1', credentials=credentials)
  build_info = cloudbuild.projects().builds().create(projectId=PROJECT_ID,
                                                     body=build_body).execute()
  build_id = build_info['metadata']['build']['id']

  print('Logs:', get_logs_url(build_id), file=sys.stderr)


if __name__ == '__main__':
  main()
