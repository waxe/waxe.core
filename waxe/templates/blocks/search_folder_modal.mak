<div class="modal fade">
  <div class="modal-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h4 class="modal-title">Select folder</h4>
      </div>
      <div class="modal-body">
        <div class="waxe-modal-breadcrumb breadcrumb">
          ${breadcrumb|n}
        </div>
        <div class="waxe-modal-content">
          ${content|n}
        </div>
      </div>
      <div class="modal-footer">
        <form class="form-search-folder form-inline">
          <input type="hidden" class="relpath" name="search-folder" value="${relpath}" />
          <input type="submit" class="btn btn-default" value="Select current folder" />
          <a href="#" class="btn" data-dismiss="modal">Cancel</a>
        </form>
      </div>
    </div>
  </div>
</div>
