$(function () {
    $('.modal.addnew').on('click', '.btn-close', function () {
        $(this).closest('.modal').modal('hide')
    })

    $('table').on('click','.deleteItem', function() {
        $(this).closest('tr').remove()
    })
})

