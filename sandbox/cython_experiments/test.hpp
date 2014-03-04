#include<iostream>


// mimic openms setup

class MSSpectrumMock {

    // aka MSSPectrum from OpenMS

    private:
        int i_;

    public:
        MSSpectrumMock(int i): i_(i) { };

        int get() { return i_; };
};


class ICallBack {

public:
    // aka Callable CppContainererface
    virtual void call(const MSSpectrumMock & i) = 0;

};


class Caller {

    // aka MzXML File reader

    private:
        ICallBack * callee_;

    public:
        Caller(ICallBack * c): callee_(c) { };

        void run (){
            MSSpectrumMock i1(1);
            MSSpectrumMock i2(2);
            callee_->call(i1);
            callee_->call(i2);
            callee_->call(i1);
            callee_->call(i2);
        }

};

// pyopenms helpers in c++

extern PyObject * wrap_cpp_class(MSSpectrumMock *p);

class PythonCallBack: virtual public ICallBack  {
    private:
        PyObject *fun_;
        PyObject  *(*conv_)(const MSSpectrumMock *);

    public:
         PythonCallBack(PyObject *fun, PyObject *(*conv)(const MSSpectrumMock *)): fun_(fun), conv_(conv) {
            Py_INCREF(fun_);
         };

         ~PythonCallBack() {
             Py_DECREF(fun_);
         };


        virtual void call(const MSSpectrumMock & i)
        {
            PyObject_CallFunctionObjArgs(fun_, conv_(&i), NULL);
        }

};
