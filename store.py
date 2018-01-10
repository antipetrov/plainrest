#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import logging
import warnings
import datetime
import time
from collections import namedtuple

import tarantool

CacheRecord = namedtuple('CacheRecord', ('key','value','ctime', 'ttl'))
DataRecord = namedtuple('DataRecord', ('key','value'))

warnings.simplefilter("ignore")

class StoreError(Exception):
    pass

class StoreTarantool(object):
    
    def __init__(self, 
                 host='localhost', 
                 port=3301, 
                 user='score_user', 
                 password='score_pass',
                 reconnect_max_attempts=10,
                 reconnect_delay=1, #seconds
                 connection_timeout=10, # seconds
                 ):

        self._host = host        
        self._port = port
        self._user = user
        self._password = password
        self._reconnect_max_attempts = reconnect_max_attempts
        self._reconnect_delay = reconnect_delay
        self._connection_timeout = connection_timeout

        self.db = None
        self._refresh_connection()
        
        # todo: create spaces if none
        self.data_space = self.db.space('data')
        self.cache_space = self.db.space('cache')

    def _refresh_connection(self):
        if self.db:
            try:
                ping = self.db.ping()
            except NetworkError as e:
                logging.error('tarantool connection error: %s', e.message)
                self.db = None
       
        if not self.db:
            try:
                self.db = tarantool.Connection(self._host, self._port, 
                                               user=self._user, 
                                               password=self._password,
                                               socket_timeout=self._connection_timeout, 
                                               reconnect_max_attempts=self._reconnect_max_attempts,
                                               reconnect_delay=self._reconnect_delay
                                               )
            except tarantool.error.NetworkError as e:
                logging.error('tarantool connection error: %s', e.message)    
                self.db = None
                raise StoreError('tarantool error: %s', e.message)


    def get(self, key):
        self._refresh_connection()

        response = self.data_space.select(key)
        if not len(response.data):
            return None

        rec = DataRecord(*response[0])
        return rec.value


    def set(self, key, value):
        self._refresh_connection()

        return self.data_space.replace((key, value))


    def cache_get(self, key):
        self._refresh_connection()

        response = self.cache_space.select(key)
        if not len(response.data):
            return None

        rec = CacheRecord(*response.data[0])

        ctime = int(time.mktime(datetime.datetime.utcnow().timetuple()))
        if rec.ttl > 0 and ctime - rec.ctime >= rec.ttl:
            return None
        else:
            return rec.value


    def cache_set(self, key, value, ttl=0):
        self._refresh_connection()
        ctime = int(time.mktime(datetime.datetime.utcnow().timetuple()))

        return self.cache_space.replace((key, value, ctime, ttl))