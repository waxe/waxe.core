% if opened_files:
<div class="panel panel-default">
  <div class="panel-heading">Last opened files</div>
  <div class="panel-body">
    % for f in opened_files:
      <a href="${request.custom_route_path('edit', _query=[('path', f.path)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', f.path)])}">${f.path}</a><br />
    % endfor
  </div>
</div>
% endif
% if commited_files:
<div class="panel panel-default">
  <div class="panel-heading">Last commited files</div>
  <div class="panel-body">
    % for f in commited_files:
      <a href="${request.custom_route_path('edit', _query=[('path', f.path)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', f.path)])}">${f.path}</a><br />
    % endfor
  </div>
</div>
% endif
