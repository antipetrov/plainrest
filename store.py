#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# 
import logging
import tarantool



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
                raise


    def get(self, key):
        self._refresh_connection()

        rec = self.data_space.select(key)
        if not len(rec.data):
            return None
        
        return rec[0][1]


    def set(self, key, value):
        self._refresh_connection()

        return self.data_space.replace((key, value))


    def cache_get(self, key):
        self._refresh_connection()

        rec = self.cache_space.select(key)
        if not len(rec.data):
            return None

        return rec[0][1]


    def cache_set(self, key, value):
        self._refresh_connection()

        return self.cache_space.replace((key, value))

# s:create_index('primary', {type='hash', parts={1, 'string'}})