-- ==============================================================================
-- JINJA MAKRO: safe_divide
-- Ochrana proti dělení nulou v analytických výpočtech
-- ==============================================================================

{% macro safe_divide(citatel, jmenovatel) %}
    round({{ citatel }} / nullIf({{ jmenovatel }}, 0), 2)
{% endmacro %}
