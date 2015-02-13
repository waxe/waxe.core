% if opened_files:
<div class="panel panel-default">
  <div class="panel-heading">Last opened files</div>
  <div class="panel-body">
    % for f in opened_files:
      % if f.iduser_owner:
        ## No data-href here since we need to reload all the page to make sure
        ## the current login is the right in the menu bar
        <a href="${request.route_path('edit', login=f.user_owner.login, _query=[('path', f.path)])}">${f.path}</a> (${f.user_owner.login})
      % else:
        <a href="${request.custom_route_path('edit', _query=[('path', f.path)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', f.path)])}">${f.path}</a>
      % endif
      <br />
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
