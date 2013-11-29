<div class="ui-layout-center">
% if files_data:
  <form class="diff" data-action="${request.route_path('versioning_dispatcher_json', method='diff')}" action="${request.route_path('versioning_dispatcher', method='diff')}" method="GET">

  <div>
	Select: <a href="#" class="select-all">All</a> / <a href="#" class="select-none">None</a>
  </div>
  <br />
  <ul class="list-unstyled">
  % for status, label_class, f, link, json_link in files_data:
    <li>
          <input type="checkbox" checked="checked" name="filenames" value="${f}" />
      <span class="label ${label_class}">${status}</span>
      <a href="${link}" data-href="${json_link}">${f}</a>
    </li>
  % endfor
  </ul>
    <input type="submit" value="Generate diff" class="multiple-diff-submit" />
% endif
</div>
