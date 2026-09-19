from Cython.Build import cythonize
from setuptools import Extension, setup

extensions = [
    Extension("agent_accel", ["agent_accel.pyx"]),
    Extension(
        "search_accel",
        ["search_accel.pyx"],
        extra_compile_args=["-O3"],  # tối ưu tốc độ cho module search nặng
    ),
]

setup(ext_modules=cythonize(extensions, language_level=3))
