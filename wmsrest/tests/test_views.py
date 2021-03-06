# -*- coding: utf-8 -*-
import os
from django.urls import reverse
from django.conf import settings
from django.core.cache import caches
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from wms.models import UGridDataset, UnidentifiedDataset, Dataset, SGridDataset, UGridTideDataset

from wms.tests import resource_path
from wms import logger  # noqa


class SciwmsAPITestCase(APITestCase):

    def tearDown(self):
        super().tearDown()
        for c in settings.CACHES.keys():
            caches[c].clear()


class TestDatasetCreate(SciwmsAPITestCase):

    def setUp(self):
        User.objects.all().delete()
        self.username = 'tester_tdl'
        self.user_email = 'tester_tdl@email.com'
        self.pwd = 'password'
        self.user = User.objects.create(username=self.username, email=self.user_email, password=self.pwd)
        self.ac = APIClient()
        self.ac.force_authenticate(user=self.user)
        self.url = reverse('dataset-list')

    def test_view_post_response(self):
        test_data = {
            'uri': 'fake_file_3.nc',
            'name': 'a third fake file',
            'title': 'some title',
            'abstract': 'a third fake abstract',
            'keep_up_to_date': False,
            'update_every': 3600,
            'display_all_timesteps': False,
            'type': 'ugrid'
        }
        response = self.ac.post(self.url, test_data, format='json')
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['update_every'], 3600)
        self.assertEqual(response.data['name'], 'a third fake file')

    def test_view_post_response_with_layers(self):
        test_data = {
            'uri': 'fake_file_4.nc',
            'name': 'a fourth fake file',
            'title': 'some title',
            'abstract': 'a fourth fake abstract',
            'keep_up_to_date': False,
            'update_every': 3600,
            'display_all_timesteps': False,
            'type': 'sgrid'
        }
        response = self.ac.post(self.url, test_data, format='json')
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['update_every'], 3600)


class TestDatasetDetail(SciwmsAPITestCase):

    def setUp(self):
        self.username = 'tester_tdd'
        self.user_email = 'tester_tdd@email.com'
        self.pwd = 'password'
        self.user, _ = User.objects.get_or_create(username=self.username, defaults=dict(email=self.user_email, password=self.pwd))
        self.dataset_1, _ = UGridDataset.objects.get_or_create(
            name='fake data 1',
            defaults=dict(
                uri='fake_file_1.nc',
                title='some title 1',
                abstract='some abstract 1',
                keep_up_to_date=False
            )
        )
        self.ac = APIClient()
        self.ac.force_authenticate(user=self.user)
        self.url = reverse('dataset-detail', kwargs={'pk': self.dataset_1.pk})

    def test_get_dataset(self):
        response = self.ac.get(self.url)
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_200_OK)
        resp_uri = response.data['uri']
        self.assertEqual(resp_uri, 'fake_file_1.nc')

    def test_patch_dataset(self):
        new_filename = 'updated_file_1.nc'
        test_data = {
            'uri': new_filename,
            'keep_up_to_date': True,
            'update_every': 7200,
            'display_all_timesteps': True,
        }
        response = self.ac.patch(self.url, test_data, format='json')
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_200_OK)
        resp_uri = response.data['uri']
        self.assertEqual(resp_uri, new_filename)
        self.assertEqual(response.data['update_every'], 7200)
        self.assertEqual(response.data['keep_up_to_date'], True)
        self.assertEqual(response.data['display_all_timesteps'], True)

    def test_delete_dataset(self):
        response = self.ac.delete(self.url)
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_204_NO_CONTENT)


class TestUnidentifiedDataset(SciwmsAPITestCase):

    def setUp(self):
        UnidentifiedDataset.objects.all().delete()
        Dataset.objects.all().delete()
        self.username = 'tester_tdd'
        self.user_email = 'tester_tdd@email.com'
        self.pwd = 'password'
        self.user, _ = User.objects.get_or_create(username=self.username, defaults=dict(email=self.user_email, password=self.pwd))
        self.dataset_1, _ = UnidentifiedDataset.objects.get_or_create(
            name='fake data 1',
            defaults=dict(
                uri='fake_file_1.nc',
            )
        )
        self.dataset_2, _ = UnidentifiedDataset.objects.get_or_create(
            name='fake data 2',
            defaults=dict(
                uri='fake_file_2.nc',
            )
        )
        self.ac = APIClient()
        self.ac.force_authenticate(user=self.user)

    def test_list_unid(self):
        url = reverse('unid-list')
        response = self.ac.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['uri'], self.dataset_1.uri)
        self.assertEqual(response.data[1]['uri'], self.dataset_2.uri)
        assert UnidentifiedDataset.objects.count() == 2

    def test_get_unid(self):
        url = reverse('unid-detail', kwargs={'pk': self.dataset_1.pk})
        response = self.ac.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uri'], self.dataset_1.uri)

        url = reverse('unid-detail', kwargs={'pk': self.dataset_2.pk})
        response = self.ac.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uri'], self.dataset_2.uri)
        assert UnidentifiedDataset.objects.count() == 2

    def test_put_unid(self):
        new_filename = 'updated_file_1.nc'
        test_data = {
            'uri': new_filename,
            'name': 'some new name',
            'messages': 'hello'
        }
        url = reverse('unid-detail', kwargs={'pk': self.dataset_1.pk})
        response = self.ac.put(url, test_data, format='json')
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uri'], new_filename)
        self.assertEqual(response.data['name'], 'some new name')
        self.assertEqual(response.data['messages'], 'hello')
        assert UnidentifiedDataset.objects.count() == 2

    def test_delete_unid(self):
        url = reverse('unid-detail', kwargs={'pk': self.dataset_1.pk})
        response = self.ac.delete(url)
        status_code = response.status_code
        self.assertEqual(status_code, status.HTTP_204_NO_CONTENT)
        assert UnidentifiedDataset.objects.count() == 1


class TestAddUnidentifiedDataset(SciwmsAPITestCase):

    def setUp(self):
        self.username = 'tester_tdd'
        self.user_email = 'tester_tdd@email.com'
        self.pwd = 'password'
        self.user, _ = User.objects.get_or_create(username=self.username, defaults=dict(email=self.user_email, password=self.pwd))
        self.ac = APIClient()
        self.ac.force_authenticate(user=self.user)
        UnidentifiedDataset.objects.all().delete()
        Dataset.objects.all().delete()

    def tearDown(cls):
        UnidentifiedDataset.objects.all().delete()
        Dataset.objects.all().delete()

    def test_add_unidentifiable(self):
        params = dict(name='test_unidientified', uri='this_is_not_anything.nc')
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 201
        assert UnidentifiedDataset.objects.count() == 1
        assert Dataset.objects.count() == 0

    def test_add_unidenified_name_conflict(self):
        params = dict(name='test_unidientified', uri='this_is_not_anything.nc')
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 201
        assert UnidentifiedDataset.objects.count() == 1
        assert Dataset.objects.count() == 0

        params = dict(name='test_unidientified', uri='this_is_still_not_anything.nc')
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 400
        assert UnidentifiedDataset.objects.count() == 1
        assert Dataset.objects.count() == 0

    def test_add_ugrid(self):
        params = dict(name='test_ugrid', uri=os.path.join(resource_path, 'selfe_ugrid.nc'))
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 201
        assert UnidentifiedDataset.objects.count() == 0
        assert UGridDataset.objects.count() == 1

    def test_add_ugrid_name_conflict(self):
        params = dict(name='test_ugrid', uri=os.path.join(resource_path, 'selfe_ugrid.nc'))
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 201
        assert UnidentifiedDataset.objects.count() == 0
        assert UGridDataset.objects.count() == 1

        params = dict(name='test_ugrid', uri=os.path.join(resource_path, 'selfe_ugrid.nc'))
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 400
        assert UnidentifiedDataset.objects.count() == 0
        assert UGridDataset.objects.count() == 1

    def test_add_sgrid(self):
        params = dict(name='test_sgrid', uri=os.path.join(resource_path, 'coawst_sgrid.nc'))
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 201
        assert UnidentifiedDataset.objects.count() == 0
        assert SGridDataset.objects.count() == 1

    def test_add_ugridtide(self):
        params = dict(name='test_ugridtide', uri=os.path.join(resource_path, 'shinnecock.nc'))
        response = self.ac.post(reverse('unid-list'), params)
        assert response.status_code == 201
        assert UnidentifiedDataset.objects.count() == 0
        assert UGridTideDataset.objects.count() == 1
