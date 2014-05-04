% for path, href, data_href, excerpt in data:

  <a href="${href}" data-href="${data_href}"><i class="glyphicon glyphicon-file"></i>${path}</a>
  <p>${excerpt|n}</p>

% endfor
