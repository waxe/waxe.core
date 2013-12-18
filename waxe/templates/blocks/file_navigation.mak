<ul id="file-navigation" class="list-unstyled" data-path="${data['path']}"${' data-versioning-path="%s"' % versioning_status_url if versioning_status_url else ''|n}>
  % if data['previous']:
    <li><i class="glyphicon glyphicon-arrow-left"></i><a data-href="${data['previous']['data_href']}" href="${data['previous']['href']}" class="previous">${data['previous']['name']}</a></li>
	% endif
  % for dic in data['folders']:
    <li><i class="glyphicon glyphicon-folder-close"></i><a data-href="${dic['data_href']}" href="${dic['href']}" class="folder" data-relpath="${dic['data_relpath']}">${dic['name']}</a></li>
  % endfor
  % for dic in data['filenames']:
    <li><i class="glyphicon glyphicon-file"></i><a data-href="${dic['data_href']}" href="${dic['href']}" class="file" data-relpath="${dic['data_relpath']}">${dic['name']}</a></li>
  % endfor
</ul>


% if versioning_status_url:
<div class="alert alert-info versioning-legend">
<p><strong>Legend of the different colors:</strong></p>
<br />
<ul class="list-unstyled">
  <li class="versioning-modified">
	<i class="glyphicon glyphicon-file"></i>
	This file/folder is modified.
  </li>
  <li class="versioning-conflicted">
	<i class="glyphicon glyphicon-file"></i>
	This file is conflicted. It comes when someone else update the same part of XML than you, you need to fix it.
  </li>
  <li class="versioning-unversioned">
	<i class="glyphicon glyphicon-file"></i>
	This file/folder is new.
  </li>
</ul>
</div>
% endif
