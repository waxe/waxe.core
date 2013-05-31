<ul id="file-navigation" data-path="${data['path']}">
  % if data['previous']:
    <li><a data-href="${data['previous']['data_href']}" href="${data['previous']['href']}" class="previous">${data['previous']['name']}</a></li>
	% endif
  % for dic in data['folders']:
    <li><a data-href="${dic['data_href']}" href="${dic['href']}" class="folder">${dic['name']}</a></li>
  % endfor
  % for dic in data['filenames']:
    <li><a data-href="${dic['data_href']}" href="${dic['href']}" class="file">${dic['name']}</a></li>
  % endfor
</ul>
