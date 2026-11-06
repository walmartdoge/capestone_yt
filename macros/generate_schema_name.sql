{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.user }}_{{ project_name }}_staging
    {%- else -%}
        {{ target.user }}_{{ project_name }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
