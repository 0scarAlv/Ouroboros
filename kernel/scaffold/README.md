# Module scaffold

`python manage.py startmodule <name> --model <Model> --audit <0|1|2>` renders
the files in `module/` into `apps/<name>/`. These files are the reference
module: they show how a module is laid out and they are kept working by
`kernel/tests/test_startmodule.py`, which generates a module at every audit
level and runs its tests.

Files end in `-tpl` so Python and pytest ignore them; they are rendered with
the Django template engine (autoescape off) and the suffix is dropped.
