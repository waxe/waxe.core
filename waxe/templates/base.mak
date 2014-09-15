<!DOCTYPE html>
<head>
  <title>Waxe</title>
  <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
  <link rel="stylesheet" type="text/css" href="${request.static_url('waxe:static/font-awesome/css/font-awesome.min.css')}" />
  <link rel="stylesheet" type="text/css" href="${request.static_url('waxe:static/css/waxe.css')}" />
  <script type="text/javascript" src="${request.static_url('waxe:static/js/waxe.js')}"></script>
  <script type="text/javascript" src="${request.static_url('waxe:static/ckeditor/ckeditor.js')}"></script>
  <script type="text/javascript" src="${request.static_url('waxe:static/ckeditor/adapters/jquery.js')}"></script>
  <script type="text/javascript">
    CKEDITOR.disableAutoInline = true;
    CKEDITOR.config.enterMode = CKEDITOR.ENTER_BR;
  </script>
</head>
  ${next.body()}
</html>
