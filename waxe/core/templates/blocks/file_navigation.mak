<div class="row" style="margin-right: 0; margin-left: 0;">
<div class="col-md-8">
  <div class="file-navigation"${' data-versioning-path="%s"' % versioning_status_url if versioning_status_url else ''|n}>
    ${content|n}
  </div>
</div>
% if last_files:
<div class="col-md-4">
  ${last_files|n}
</div>
% endif
</div>


% if versioning_status_url:
<div class="alert alert-info versioning-legend">
<p><strong>Legend of the different colors:</strong></p>
<br />
<ul class="list-unstyled">
  <li>
	<i class="fa fa-file-excel-o"></i>
	This file/folder is normal, no modification has been done.
  </li>
  <li class="versioning-modified">
	<i class="fa fa-file-excel-o"></i>
	This file/folder is modified.
  </li>
  <li class="versioning-conflicted">
	<i class="fa fa-file-excel-o"></i>
	This file is conflicted. It comes when someone else update the same part of XML than you, you need to fix it.
  </li>
  <li class="versioning-unversioned">
	<i class="fa fa-file-excel-o"></i>
	This file/folder is new.
  </li>
  <li class="versioning-other">
	<i class="fa fa-file-excel-o"></i>
	This status should not come to you. If it's the case please make an update of the repository. If the problem persists contact your administrator.
  </li>
</ul>
</div>
% endif