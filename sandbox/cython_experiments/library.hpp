#ifndef __library_hpp_included__
#define __library_hpp_included__

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
    virtual int call(const MSSpectrumMock & i) = 0;

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
#endif

