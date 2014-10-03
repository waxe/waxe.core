<div class="row">
<div class="col-md-4">

<form data-action="${request.custom_route_path('search_json')}">
  <div class="form-group">
    <input type="text" class="form-control" id="search" name="search" placeholder="Search" value="${search}">
  </div>

  <div class="form-group">
    <input type="text" class="form-control" id="search-path" name="path" placeholder="Root (search in all the files)" value="${relpath}">
    <a data-href="${request.custom_route_path('search_folder_json')}" href="#">select folder</a>
  </div>

  <button type="submit" class="btn btn-default">Submit</button>

  <br />
  <br />
  <br />

  ${result|n}

  % if data:
    % for path, excerpt in data:
      <i class="fa fa-file-excel-o"></i>
      <a href="${request.custom_route_path('edit',_query=[('path', path)])}" data-href="${request.custom_route_path('edit_json',_query=[('path', path)])}"> ${path}</a>
      <p>${excerpt|n}</p>

    % endfor
    ${pageobj.pager()|n}
  % endif
</form>
</div>
</div>
