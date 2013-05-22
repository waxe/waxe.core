<div class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
    <h3>New file</h3>
  </div>
  <div class="modal-body">
	<label>Choose a dtd:</label>
	<select data-href="/get-tags.json" class="dtd-urls input-xxlarge">
	% for dtd_url in dtd_urls:
	  <option value="${dtd_url}">${dtd_url}</option>
	% endfor
	</select>
	<label>Choose a root tag</label>
	<select class="dtd-tags input-xxlarge">
	  % for tag in tags:
	    <option value="${tag}">${tag}</option>
	  % endfor
	</select>
  </div>
  <div class="modal-footer">
    <a href="#" class="btn" data-dismiss="modal">Cancel</a>
    <a data-href="/new.json" class="btn btn-primary submit">Create</a>
  </div>
</div>'
