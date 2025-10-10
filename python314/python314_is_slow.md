# Python 3.14 (π) for ML? Maybe Not So Fast.

Following the recent release of Python 3.14 (π), many developers have reported noticeable speedups over past versions. This has left ML engineers and data scientists wondering: does the new JIT compiler offer any meaningful performance improvements for common machine learning tasks? My dependable interpreter has been Python 3.11 for three years now, so I was curious if it was finally time to migrate my projects.

After running a few of my old codebases without seeing any improvement, I decided to benchmark one of the most fundamental functions in machine learning: the sigmoid function. It can be implemented using either exp() or tanh(), and since performance can vary by compiler, I tested both across different Python versions.

The results were unsurprising but also underwhelming. In nearly all of my tests, Python 3.14 was slower than both Python 3.11 and even 3.10 (now five years old). Worse still, enabling the new JIT in 3.14 completely tanked performance, even after I discounted its warmup time. This isn't as shocking as it sounds. Most ML work relies on libraries like NumPy, Pandas, and PyTorch which are Python wrappers around highly optimized native codes like C, C++ and Fortran. Since the heavy lifting happens at this native level, improvements to the Python interpreter itself often don't translate to significant gains for these workflows.

The real discovery, however, came when I ran the same pure-Python code on PyPy. With its JIT enabled, PyPy was nearly four times faster than any version of standard CPython. 

So I guess, I won't be rushing to migrate my ML projects to Python 3.14. The real lesson was a powerful reminder of PyPy's strength. If you have a workflow that can run entirely within PyPy, the speed benefits are undeniable.
