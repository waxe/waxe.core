% for path, href, data_href, excerpt in data:

  <a href="${href}" data-href="${data_href}"><i class="glyphicon glyphicon-file"></i>${path}</a>
  <p>${excerpt|n}</p>

% endfor

<ul class="pagination">
% for p in pages:
    % if p == curpage:
      <li class="active">
        <a href="#">${p}</a>
      </li>
    % else:
      <li>
        <a href="${search_url(p)}" data-href="${search_url(p, json=True)}">${p}</a>
      </li>
    % endif
% endfor
</ul>
