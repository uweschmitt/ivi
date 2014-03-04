#include "library.hpp"
#include <iostream>
#include <strstream>

template <class T>
class PythonCallBack: virtual public ICallBack  {
    private:
        PyObject *fun_;
        PyObject  *(*conv_)(const T *);

    public:
         PythonCallBack(PyObject *fun, PyObject *(*conv)(const T *)): fun_(fun), conv_(conv) {
            Py_INCREF(fun_);
         };

         ~PythonCallBack() {
             Py_DECREF(fun_);
         };


        virtual int call(const T & i)
        {
            PyObject * converted = conv_(&i);
            PyObject * result = PyObject_CallFunctionObjArgs(fun_, conv_(&i), NULL);
            PyObject * fun_as_str = PyObject_Str(fun_);
            if (result == NULL) {
                std::strstream msg;
                msg << "calling " << PyString_AsString(PyObject_Str(fun_)) << " with argument ";
                msg << PyString_AsString(PyObject_Str(converted)) << "failed" ;
                throw msg.str();
            }
            return 1;
        }

};
