# coding: utf-8
import os, sys, re
import importlib
import batchmp.fstools.rename as r

importlib.reload(r)
ren = r.Renamer
ren.add_date('.', max_depth=0, filter_dirs=True, include = '[!.]*')
