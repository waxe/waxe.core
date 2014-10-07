% if files:
  <div class="panel panel-default">
    <div class="panel-heading">The repository has been updated! List of files you have fetched:</div>
    <div class="panel-body">
      <ul class="list-unstyled">
      % for status, f in files:
        <li>
        <span class="label label-${status}">${status}</span>
          % if status in [STATUS_ADDED, STATUS_MODIFED]:
        <a href="${request.custom_route_path('edit', _query=[('path', f)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', f)])}">${f}</a>
        % else:
          ${f}
        % endif
        </li>
        % endfor
      </ul>
      </form>
    </div>
  </div>
% else:
    The repository was already updated!
% endif
