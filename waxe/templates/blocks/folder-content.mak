% if previous:
  <i class="fa fa-folder-o"></i>
  ${previous_tag|n}
% endif
<div class="row">
  % for tag in folder_tags:
    <div class="col-md-6">
      <i class="fa fa-folder-o"></i>
      ${tag|n}
    </div>
  % endfor
  % for tag in filename_tags:
    <div class="col-md-6">
      <i class="fa fa-file-excel-o"></i>
      ${tag|n}
    </div>
  % endfor
</div>
