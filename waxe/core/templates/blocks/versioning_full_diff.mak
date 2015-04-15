<div>
  <form data-action="${request.custom_route_path('versioning_update_texts_json')}">
  % for index, (filename, diff) in enumerate(files):

        <input type="hidden" name="data:${index}:filename" value="${filename}" />
      <a href="${request.custom_route_path('edit', _query=[('path', filename)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', filename)])}">Edit ${filename}</a>
    <br />
    <br />
        <textarea name="data:${index}:filecontent" class="hidden">Something</textarea>
      ${diff|n}
      <br />
      <br />

  % endfor
    % if can_commit:
      <button class="btn btn-success" type="submit" name="commit">Commit</button>
    % endif
    <button type="submit">Submit</button>
  </form>
</div>
