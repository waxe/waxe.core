<ul id="file-navigation" class="list-unstyled" data-path="${data['path']}">
  % if data['previous']:
    <li><i class="glyphicon glyphicon-arrow-left"></i><a data-href="${data['previous']['data_href']}" href="${data['previous']['href']}" class="previous">${data['previous']['name']}</a></li>
	% endif
  % for dic in data['folders']:
    <li><i class="glyphicon glyphicon-folder-close"></i><a data-href="${dic['data_href']}" href="${dic['href']}" class="folder">${dic['name']}</a></li>
  % endfor
  % for dic in data['filenames']:
    <li><i class="glyphicon glyphicon-file"></i><a data-href="${dic['data_href']}" href="${dic['href']}" class="file">${dic['name']}</a></li>
  % endfor
</ul>
