<ul id="file-navigation" data-path="${path}">
  % for css_class, name, href in data:
    <li><a data-href="${href}" class="${css_class}">${name}</a></li>
  % endfor
</ul>
