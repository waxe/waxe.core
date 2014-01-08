<form data-action="${request.custom_route_path('versioning_dispatcher_json', method='update_texts')}" action="${request.custom_route_path('versioning_dispatcher', method='update_texts')}" method="POST" class="editable-diff">
  % for index, (filename, diff) in enumerate(files):

    % if can_commit:
      <input type="hidden" name="commit" value="1" />
    % endif
        <input type="hidden" name="data:${index}:filename" value="${filename}" />
      <a href="${request.custom_route_path('edit', _query=[('path', filename)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', filename)])}">Edit ${filename}</a>
    <br />
    <br />
        <textarea name="data:${index}:filecontent" class="hidden"></textarea>
      ${diff|n}
      <br />
      <br />

  % endfor
  <input type="submit" value="Save${' and commit' if can_commit else ''}" />
  </form>
