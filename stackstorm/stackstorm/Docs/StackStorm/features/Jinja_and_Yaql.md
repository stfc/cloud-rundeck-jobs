# YAQL
YAQL (Yet Another Query Language) is an Openstack project and allows complex data querying and transformation.

Orquesta supports YAQL expressions.
YAQL expressions are wrapped in between ` <% YAQL expression %> `


## Dictionaries

To create a dictionary, use the `dict` function.
`<% dict(a=>"Hello", b=>"World") %>` returns `{'a':"Hello", 'b':"World"}`

Dictionaries can be accessed list this (assuming the above stored in variable: `dict1`):
`<% ctx(dict1).keys() %>` returns keys as a list `['a', 'b']`

`<% ctx(dict1).values() %>` returns values as a list `["Hello", "World"]`

`<% ctx(dict1).get(b) %>` returns string `"World"`

`<% ctx(dict1).get(x, false) %>` returns `False` because `x` is not in keys

Can add dictionaries like:
`<% dict(a=>"Hello", b=>"World") + dict(c=>"Goodbye", d=>"Universe") %>`


## List

To create a list, use the `list` function
`<% list(1, 2, 3) %>` returns [1, 2, 3]
`<% list("abc", "def") %>` returns `[abc, def]`

Can add lists like:
`<% list(a=>"Hello", b=>"World") + list(c=>"Goodbye", d=>"Universe") %>`

Can access via index like:
`<% ctx(list1)[0] %>` returns String `abc`

## Queries

YAQL expressions can make some sample queries on dictionary

example dictionary:
```
{"greetings": [
  {
    "a": "Hello"
    "b": "World"
  }
  {
    "a": "Greetings"
    "b": "StackStorm"
  }
  {
    "a": "Hi"
    "b": "Universe"
  }
]}
```

`<% ctx(greetings).select($.a) %>` returns the list of `a` values => `["Hello", "Greetings", "Hi"]`

`<% ctx(greetings).select($.a = "Greetings").select($.b) %>` returns only `b` value where `a` matches "Greetings" => `[StackStorm]`

`<% let(my_greeting_arg => "Greetings") -> ctx(greetings).where($.a = $.my_greeting_arg).select($.b) %>` returns the same thing as above => `[StackStorm]`

see https://docs.stackstorm.com/orquesta/yaql.html for more info

# Usage in Orquesta

The following Orquesta workflow will output "hello world" - the first item in the "messages" list

```
version: 1.0

vars:
  - stdout: null
  - messages:
    - "Hello World"
    - "Goodbye Universe"
    - "Yo Stackstorm"

output:
  - stdout: <% ctx().stdout %>

tasks:
  task1:
    action: core.echo message=<% ctx().message[0] %>
    next:
      - when: <% succeeded %>    
        publish:
          - stdout: <% result().stdout %>
```

# Jinja
Jinja is a templating engine, an alternative to YAQL.
Used to manipulate parameter values in StackStorm by allowing you to refer to
other parameters, applying filters or refer to system specific constructs

Jinja expression are wrapped in-between `{{ Jinja expression }}`.
Uses `{% %}` for Statements.

A Jinja template contains variables and/or expressions, which get replaced with
values when a template is rendered.

# Jinja Usage

Jinja can be used in a similar way to YAQL.

The following Orquesta workflow will output "hello world" - the first item in the "messages" list

```
version: 1.0

vars:
- stdout: null
- messages:
    - "hello world"
    - "goodbye universe"
    - "yo stackstorm"
output:
- stdout: '{{ ctx().stdout}}'

tasks:
task1:
  action: core.noop
  next:
    - when: <% succeeded() %>
      publish:
        - stdout: '{{ ctx().messages[0]}}'

```

# Datastore
Can user `{{ st2kv.system.foo }}` to access key `foo` from the datastore

When accessing datastore data, it will be outputted as strings, to represent complex data structures such as `dicts` and `lists`, must convert the data structure to JSON before storing the data, then parse it when retrieving the data.

Can use the filter `my_filter` on `foo`, you use the pipe operator `{{ foo | my_filter }}`.

Jinja will convert all inputs to text, to do manipulations happen on that value. The necessary casting at the end is done by StackStorm based on information provided in YAML (`type` field in action parameters). The casting is a best-effort casting

See https://docs.stackstorm.com/reference/jinja.html#custom-jinja-filters for more information
