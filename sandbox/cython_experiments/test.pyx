# distutils: language=c++

from cython.operator import dereference as deref


# declare helpers first (else cython parsre crashes)

cdef extern from "helper.hpp":

    cdef cppclass PythonCallBack[T]:
        PythonCallBack(object fun, object(*conv)(const T *)) 
        int call(const T &) except +



# declare original libary after helpers

cdef extern from "library.hpp":

    cdef cppclass _MSSpectrumMock "MSSpectrumMock":
        _MSSpectrumMock(int)
        _MSSpectrumMock(_MSSpectrumMock)
        int get()

    cdef cppclass Caller:
        Caller(PythonCallBack[_MSSpectrumMock] *)
        void run() except +


# wrapp c++ class which is callback argument

cdef class MSSpectrumMock:

    cdef _MSSpectrumMock * inst

    def __init__(self):
        pass

    def __dealloc__(self):
        del self.inst

    def get(self):
        return deref(self.inst).get()

# this is a little helper, remenber: another level of indirection is the solution to many
# problems :)

cdef object wrap_cpp_class(const _MSSpectrumMock * i):

    cdef MSSpectrumMock iw = MSSpectrumMock.__new__(MSSpectrumMock)
    iw.inst = new _MSSpectrumMock(deref(i))
    return iw


# now we assemble our stuff

def run_with(python_call_back):

    cdef PythonCallBack[_MSSpectrumMock] * callback 
    callback = new PythonCallBack[_MSSpectrumMock](python_call_back, wrap_cpp_class)

    cdef Caller * c = new Caller(callback)
    c.run()

    del c
    del callback


# lets test it !

def callme(MSSpectrumMock iw):
    print "this is python", iw, iw.gext()


def run():
    run_with(callme)















