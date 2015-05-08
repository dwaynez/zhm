#
# Cython wrapper for the zhmalarm functions
# Copyright (C) Dwayne Zon 2015 <dwayne.zon@gmail.com> 
#
from libc.stdint cimport uint32_t

cdef extern from "zhmalarm_modules.h":
    ctypedef void (*monitoralarm_func)(int name, void *user_data)
    void zhm_monitoralarm(monitoralarm_func user_func, void *user_data) nogil
    void zhm_cleanup()
#~     void zhm_sendchar(char s)


def monitoralarm(f):
    with nogil:
        zhm_monitoralarm(callback, <void*>f)
    
def cleanup():
    zhm_cleanup()
    
#~ def sendchar(s):
#~     zhm_sendchar(s)
    
cdef void callback(int name, void *f) with gil:
    (<object>f)(name)
