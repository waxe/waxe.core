% if previous:
  <i class="fa fa-folder-o"></i>
  ${previous['link_tag']|n}
% endif
<div class="row">
  % for folder in folders:
    <div class="col-md-6">
      <i class="fa fa-folder-o"></i>
      ${folder['link_tag']|n}
    </div>
  % endfor
  % for f in filenames:
    <div class="col-md-6">
      <i class="fa fa-file-excel-o"></i>
      <a data-href="${f['data_href']}" href="">${f['name']}</a>
    </div>
  % endfor
</div>
