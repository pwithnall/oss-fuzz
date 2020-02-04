#!/usr/bin/python2
"""Build base images on Google Cloud Builder.

Usage: build_base_images.py
"""

import os
import sys
import yaml

from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build


CIFUZZ_IMAGE = 'base-cifuzz',

PROJECT_ID = 'oss-fuzz-cifuzz'
TAG_PREFIX = 'gcr.io/{0}/'.format(PROJECT_ID)


def get_steps(ci_fuzz_image):
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
  URL_FORMAT = ('https://console.developers.google.com/logs/viewer?'
                'resource=build%2Fbuild_id%2F{0}&project={1}')
  return URL_FORMAT.format(build_id, PROJECT_ID)


def main():
  options = {}
  if 'GCB_OPTIONS' in os.environ:
    options = yaml.safe_load(os.environ['GCB_OPTIONS'])

  build_body = {
      'steps': get_steps(CIFUZZ_IMAGE),
      'timeout': str(4 * 3600) + 's',
      'options': options,
      'images': [TAG_PREFIX + CIFUZZ_IMAGE],
  }

  credentials = GoogleCredentials.get_application_default()
  cloudbuild = build('cloudbuild', 'v1', credentials=credentials)
  build_info = cloudbuild.projects().builds().create(
      projectId=PROJECT_ID, body=build_body).execute()
  build_id = build_info['metadata']['build']['id']

  print >> sys.stderr, 'Logs:', get_logs_url(build_id)
  print build_id


if __name__ == '__main__':
  main()
