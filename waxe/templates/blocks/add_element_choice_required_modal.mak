<div class="modal fade">
  <div class="modal-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <form data-action="${request.custom_route_path('add_element_json')}" method="GET">
  <input type="hidden" name="dtd_url" value="${dtd_url}" />
  <input type="hidden" name="elt_id" value="${elt_id}" />
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h3>Required choices</h3>
      </div>
      <div class="modal-body">
      <h5>Some children with many choices are required:</h5>
      % for tagname in required_children:
      <div class="checkbox">
      <label><input type="radio" name="required_child" value="${tagname}"/>${tagname}</label>
      </div>
    % endfor
      </div>
      <div class="modal-footer">
        <a href="#" class="btn" data-dismiss="modal">Cancel</a>
    <input class="btn btn-primary" type="submit" value="Commit" />
      </div>
    </div>
  </form>
  </div>
</div>
