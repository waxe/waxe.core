% if conflicteds:
  <div class="panel panel-default">
    <div class="panel-heading">List of conflicted files that should be resolved:</div>
    <div class="panel-body">
      <form data-action="${request.custom_route_path('versioning_status_post_json')}" action="${request.custom_route_path('versioning_status_post')}" method="POST">
        <div>
          Select: <a href="#" class="select-all">All</a> / <a href="#" class="select-none">None</a>
        </div>
      <ul class="list-unstyled">
      % for conflicted in conflicteds:
        <li>
        <input type="checkbox" checked="checked" name="filenames" value="${conflicted.relpath}" />
        <span class="label label-${conflicted.status}">${conflicted.status}</span>
        <a href="${request.custom_route_path('versioning_edit_conflict', _query=[('path', conflicted.relpath)])}" data-href="${request.custom_route_path('versioning_edit_conflict_json', _query=[('path', conflicted.relpath)])}">${conflicted.relpath}</a>
        </li>
        % endfor
      </ul>
      <input class="btn btn-danger" type="submit" value="Revert" name="submit" data-confirm="Are you sure you want to revert the selected files? All your modifications will be deleted!" />
      </form>
    </div>
  </div>
  <br />
% endif

% if uncommitables:
  <div class="panel panel-default">
    <div class="panel-heading">List of updated files:</div>
    <div class="panel-body">
      <form data-action="${request.custom_route_path('versioning_status_post_json')}" action="${request.custom_route_path('versioning_status_post')}" method="POST">
        <div>
          Select: <a href="#" class="select-all">All</a> / <a href="#" class="select-none">None</a>
        </div>
        <ul class="list-unstyled">
          % for other in uncommitables:
            <li>
                <input type="checkbox" checked="checked" name="filenames" value="${other.relpath}" />
            <span class="label label-${other.status}">${other.status}</span>
            <a href="${request.custom_route_path('edit', _query=[('path', other.relpath)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', other.relpath)])}">${other.relpath}</a>
            </li>
            % endfor
        </ul>
        <input class="btn btn-danger" type="submit" value="Revert" name="submit" data-confirm="Are you sure you want to revert the selected files? All your modifications will be deleted!" />
        <input class="btn btn-danger" type="submit" value="Delete" name="submit" data-confirm="Are you sure you want to delete the selected files?" />
        <input class="btn btn-primary" type="submit" value="Generate diff" name="submit" />
      </form>
    </div>
  </div>
  <br />
% endif

% if others:
  <div class="panel panel-default">
    <div class="panel-heading">List of commitable files:</div>
    <div class="panel-body">
      <form data-action="${request.custom_route_path('versioning_status_post_json')}" action="${request.custom_route_path('versioning_status_post')}" method="POST">
        <div>
            Select: <a href="#" class="select-all">All</a> / <a href="#" class="select-none">None</a>
        </div>
        <ul class="list-unstyled">
        % for other in others:
          <li>
              <input type="checkbox" checked="checked" name="filenames" value="${other.relpath}" />
          <span class="label label-${other.status}">${other.status}</span>
          <a href="${request.custom_route_path('edit', _query=[('path', other.relpath)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', other.relpath)])}">${other.relpath}</a>
          </li>
          % endfor
        </ul>
        <input class="btn btn-danger" type="submit" value="Revert" name="submit" data-confirm="Are you sure you want to revert the selected files? All your modifications will be deleted!" />
        <input class="btn btn-danger" type="submit" value="Delete" name="submit" data-confirm="Are you sure you want to delete the selected files?" />
        <input class="btn btn-primary" type="submit" value="Generate diff" name="submit" />
        <input class="btn btn-success" type="submit" value="Commit" name="submit" />
      </form>
    </div>
  </div>
% endif
