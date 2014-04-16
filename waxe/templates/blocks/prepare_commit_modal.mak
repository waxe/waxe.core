<div class="modal fade">
  <div class="modal-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <form data-action="${request.custom_route_path('versioning_commit_json')}">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h3>Commit</h3>
      </div>
      <div class="modal-body">
    <h5>Choose the files you want to commit</h5>
      % for file in files:
      <div class="checkbox">
      <label><input type="checkbox" checked="checked" name="path" value="${file}"/>${file}</label>
      </div>
    % endfor
    <br />
    <h5>Enter the commit message</h5>
        <textarea class="form-control" name="msg"></textarea>
      </div>
      <div class="modal-footer">
        <a href="#" class="btn" data-dismiss="modal">Cancel</a>
    <input class="btn btn-primary" type="submit" value="Commit" />
      </div>
    </div>
  </form>
  </div>
</div>
